/**
 * POST /api/enquire
 *
 * Takes the enquiry form at /#enquire, emails it to the business through
 * Resend, and sends the visitor a confirmation.
 *
 * If RESEND_API_KEY is not set, this returns 503 and the front end falls back
 * to a prefilled mailto, so the form still reaches someone.
 */

import { Resend } from 'resend';

const MAX = { name: 120, email: 160, phone: 40, location: 60, message: 4000 };

function clean(value, limit) {
  return String(value ?? '').trim().slice(0, limit);
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const key = process.env.RESEND_API_KEY;
  const from = process.env.ENQUIRY_FROM;
  const to = (process.env.ENQUIRY_TO || '').split(',').map((s) => s.trim()).filter(Boolean);

  if (!key || !from || !to.length) {
    return res.status(503).json({
      error: 'Email delivery is not configured. Set RESEND_API_KEY, ENQUIRY_FROM and ENQUIRY_TO.'
    });
  }

  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});

  const name = clean(body.name, MAX.name);
  const email = clean(body.email, MAX.email);
  const phone = clean(body.phone, MAX.phone);
  const location = clean(body.location, MAX.location);
  const message = clean(body.message, MAX.message);

  if (!name || !email || !message) {
    return res.status(400).json({ error: 'Name, email and message are all required.' });
  }
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) {
    return res.status(400).json({ error: 'That email address does not look right.' });
  }

  const resend = new Resend(key);

  const rows = [
    ['Name', name],
    ['Email', email],
    ['Phone', phone || 'Not given'],
    ['Camp', location || 'Not given']
  ].map(([label, value]) => (
    `<tr><td style="padding:6px 18px 6px 0;color:#6b6a66;font-size:13px">${label}</td>` +
    `<td style="padding:6px 0;font-size:15px;color:#14120e">${escapeHtml(value)}</td></tr>`
  )).join('');

  const internal = `
    <div style="font-family:-apple-system,Segoe UI,sans-serif;max-width:560px">
      <p style="font-size:12px;letter-spacing:.2em;text-transform:uppercase;color:#c2551a;font-weight:700">
        New camp enquiry
      </p>
      <table style="border-collapse:collapse;margin:18px 0">${rows}</table>
      <div style="border-top:1px solid #e3ded4;padding-top:16px;white-space:pre-wrap;font-size:15px;line-height:1.65;color:#14120e">${escapeHtml(message)}</div>
    </div>`;

  const confirmation = `
    <div style="font-family:-apple-system,Segoe UI,sans-serif;max-width:560px;color:#14120e">
      <p style="font-size:16px;line-height:1.65">Hi ${escapeHtml(name.split(' ')[0])},</p>
      <p style="font-size:16px;line-height:1.65">
        Thanks for getting in touch with Revivr. We have your enquiry and someone
        will come back to you shortly.
      </p>
      <div style="border-left:2px solid #c2551a;padding-left:16px;margin:24px 0;white-space:pre-wrap;font-size:15px;line-height:1.65;color:#5a5852">${escapeHtml(message)}</div>
      <p style="font-size:16px;line-height:1.65">
        If it is urgent, call us on
        <a href="tel:+61431525118" style="color:#c2551a">0431 525 118</a>.
        We are contactable seven days, 07:00 to 22:00.
      </p>
      <p style="font-size:13px;color:#8a8780;margin-top:28px">
        Revivr: The Wellness Club<br>
        13 Fairfax Street, Sippy Downs, Queensland 4556
      </p>
    </div>`;

  try {
    const sent = await resend.emails.send({
      from,
      to,
      replyTo: email,
      subject: `Camp enquiry: ${name}${location ? ` (${location})` : ''}`,
      html: internal
    });

    if (sent.error) throw new Error(sent.error.message || 'Resend rejected the message');

    // Confirmation to the visitor is a nicety, not the job. If it fails we
    // still report success, because the business already has the enquiry.
    try {
      await resend.emails.send({
        from,
        to: email,
        subject: 'We have your Revivr enquiry',
        html: confirmation
      });
    } catch (_) { /* ignore */ }

    return res.status(200).json({ ok: true });
  } catch (err) {
    console.error('[enquire]', err);
    return res.status(502).json({ error: 'Could not send that enquiry.' });
  }
}
