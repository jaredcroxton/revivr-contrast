/**
 * POST /api/checkout  { plan: "essential" | "session" | "business" }
 *
 * Creates a Stripe Checkout Session for one of the coaching packages and
 * returns its URL for the browser to redirect to.
 *
 * If the Stripe keys or price ids are missing, this returns 503 and the front
 * end falls back to the enquiry form with the package prefilled, so the
 * Purchase button is never a dead end.
 */

import Stripe from 'stripe';

// plan key -> the env var holding its Stripe price id, and how it is billed.
const PLANS = {
  essential: { env: 'STRIPE_PRICE_ESSENTIAL', mode: 'subscription', label: 'Essential Coaching Package' },
  session:   { env: 'STRIPE_PRICE_SESSION',   mode: 'payment',      label: 'Coaching Session' },
  business:  { env: 'STRIPE_PRICE_BUSINESS',  mode: 'subscription', label: 'PT Business Coaching' }
};

function siteUrl(req) {
  if (process.env.SITE_URL) return process.env.SITE_URL.replace(/\/$/, '');
  const host = req.headers['x-forwarded-host'] || req.headers.host;
  const proto = req.headers['x-forwarded-proto'] || 'https';
  return `${proto}://${host}`;
}

export default async function handler(req, res) {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const secret = process.env.STRIPE_SECRET_KEY;
  if (!secret) {
    return res.status(503).json({ error: 'Payments are not configured. Set STRIPE_SECRET_KEY.' });
  }

  const body = typeof req.body === 'string' ? JSON.parse(req.body || '{}') : (req.body || {});
  const plan = PLANS[body.plan];
  if (!plan) return res.status(400).json({ error: 'Unknown plan.' });

  const price = process.env[plan.env];
  if (!price || !price.startsWith('price_')) {
    return res.status(503).json({ error: `Set ${plan.env} to the Stripe price id for ${plan.label}.` });
  }

  const base = siteUrl(req);

  try {
    const stripe = new Stripe(secret);
    const session = await stripe.checkout.sessions.create({
      mode: plan.mode,
      line_items: [{ price, quantity: 1 }],
      success_url: `${base}/?paid=1&plan=${encodeURIComponent(body.plan)}#pricing`,
      cancel_url: `${base}/#pricing`,
      allow_promotion_codes: true,
      billing_address_collection: 'auto',
      phone_number_collection: { enabled: true },
      metadata: { plan: body.plan, plan_label: plan.label }
    });

    return res.status(200).json({ url: session.url });
  } catch (err) {
    console.error('[checkout]', err);
    return res.status(502).json({ error: 'Could not start checkout.' });
  }
}
