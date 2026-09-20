/**
 * POST /api/webhook
 *
 * Stripe webhook. On checkout.session.completed it emails the business that a
 * coaching package has been paid for, and sends the customer a short welcome
 * so someone can book their first session.
 *
 * Point a Stripe webhook endpoint at https://YOUR-DOMAIN/api/webhook and
 * subscribe to checkout.session.completed.
 */

import Stripe from 'stripe';
import { Resend } from 'resend';

// Stripe signs the raw body, so it must not be parsed before verification.
export const config = { api: { bodyParser: false } };

function rawBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on('data', (c) => chunks.push(c));
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).end('Method not allowed');
  }

  const secret = process.env.STRIPE_SECRET_KEY;
  const signingSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!secret || !signingSecret) {
    return res.status(503).end('Webhook not configured');
  }

  const stripe = new Stripe(secret);
  let event;

  try {
    const buf = await rawBody(req);
    event = stripe.webhooks.constructEvent(buf, req.headers['stripe-signature'], signingSecret);
  } catch (err) {
    console.error('[webhook] signature check failed', err.message);
    return res.status(400).end(`Webhook Error: ${err.message}`);
  }

  if (event.type !== 'checkout.session.completed') {
    return res.status(200).json({ received: true });
  }

  const session = event.data.object;
  const label = session.metadata?.plan_label || 'a coaching package';
  const customerEmail = session.customer_details?.email;
  const customerName = session.customer_details?.name || 'there';
  const amount = session.amount_total != null
    ? `$${(session.amount_total / 100).toFixed(2)} ${String(session.currency || 'aud').toUpperCase()}`
    : 'Not recorded';

  const key = process.env.RESEND_API_KEY;
  const from = process.env.ENQUIRY_FROM;
  const to = (process.env.ENQUIRY_TO || '').split(',').map((s) => s.trim()).filter(Boolean);

  // A missing Resend setup must never fail the webhook, or Stripe will retry
  // a payment that already succeeded.
  if (key && from && to.length) {
    const resend = new Resend(key);
    try {
      await resend.emails.send({
        from,
        to,
        subject: `Paid: ${label}`,
        html: `
          <div style="font-family:-apple-system,Segoe UI,sans-serif;max-width:560px;color:#14120e">
            <p style="font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#c2551a;font-weight:700">Coaching payment received</p>
            <p style="font-size:16px;line-height:1.7">
              <strong>${escapeHtml(label)}</strong><br>
              ${escapeHtml(customerName)}<br>
              ${escapeHtml(customerEmail || 'No email recorded')}<br>
              ${escapeHtml(session.customer_details?.phone || 'No phone recorded')}<br>
              ${escapeHtml(amount)}
            </p>
            <p style="font-size:14px;color:#6b6a66">Reach out and lock in their first session.</p>
          </div>`
      });

      if (customerEmail) {
        await resend.emails.send({
          from,
          to: customerEmail,
          subject: `Your ${label} is confirmed`,
          html: `
            <div style="font-family:-apple-system,Segoe UI,sans-serif;max-width:560px;color:#14120e">
              <p style="font-size:16px;line-height:1.65">Hi ${escapeHtml(customerName.split(' ')[0])},</p>
              <p style="font-size:16px;line-height:1.65">
                Your <strong>${escapeHtml(label)}</strong> is confirmed. We will be in touch
                to lock in your first session.
              </p>
              <p style="font-size:16px;line-height:1.65">
                Want a camp as well? Pick your coast at
                <a href="https://revivr.com.au/#book" style="color:#c2551a">revivr.com.au</a>,
                or call <a href="tel:+61431525118" style="color:#c2551a">0431 525 118</a>.
              </p>
              <p style="font-size:13px;color:#8a8780;margin-top:28px">
                Revivr: The Wellness Club<br>
                13 Fairfax Street, Sippy Downs, Queensland 4556
              </p>
            </div>`
        });
      }
    } catch (err) {
      console.error('[webhook] email failed', err);
    }
  }

  return res.status(200).json({ received: true });
}
