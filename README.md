# Revivr: The Wellness Club

Scroll-film website for Revivr. The whole page opens as one continuous camera
push from a pre-dawn lagoon, through the cold plunge, into sauna heat, then
hands over to the booking content.

Live: https://revivr-contrast.vercel.app

## Layout

| Section | Job |
|---|---|
| Film | The scroll-scrubbed opening. 301 frames on a canvas. Do not edit. |
| Manifesto | What Revivr is, in the business's own words. |
| The Protocol | Cold, breath, heat, stillness. |
| A morning at camp | The timeline of a session. |
| Book a camp | The conversion moment. Three locations, three live calendars. |
| Coaching packages | Three paid packages, Stripe Checkout. |
| FAQ | The seven questions people ask before a first camp. |
| Enquire | Contact form, emailed through Resend. |
| Partners, footer | Real partner links, real contact details. |

## No dead controls

Every link and button on the page goes somewhere real, and every action that
depends on a third-party service has a working fallback:

- **Camp booking** goes straight to that location's live Newie calendar.
- **Purchase now** calls `/api/checkout`. With no Stripe keys set it falls back
  to the enquiry form with the package name prefilled, and explains why.
- **Send enquiry** posts to `/api/enquire`. If Resend is not configured or the
  request fails, it opens a prefilled email to `info@revivr.com.au` instead.
- Phone numbers are `tel:+61...` links so they dial from any phone.
- There are no social links, because the business has none published yet. Add
  them to the footer when they do.

## Connecting Resend and Stripe

Everything is scaffolded and inert until the keys are set. Copy `.env.example`
to `.env` for local work, and add the same variables in Vercel under
**Project Settings > Environment Variables**. `.env.example` explains where each
value comes from.

Short version:

1. **Resend.** Verify `revivr.com.au` as a sending domain, create an API key,
   then set `RESEND_API_KEY`, `ENQUIRY_FROM` and `ENQUIRY_TO`.
2. **Stripe.** Create the three coaching products, then set `STRIPE_SECRET_KEY`
   and the three `STRIPE_PRICE_*` variables to the price ids.
3. **Stripe webhook.** Add an endpoint at `https://YOUR-DOMAIN/api/webhook`
   subscribed to `checkout.session.completed`, and set `STRIPE_WEBHOOK_SECRET`.
   This is what emails the business when a package is paid for.

Redeploy after adding variables. Nothing else needs changing.

## API

| Route | Method | Purpose |
|---|---|---|
| `/api/enquire` | POST | Enquiry form to the business, plus a confirmation to the sender. |
| `/api/checkout` | POST | Creates a Stripe Checkout Session, returns its URL. |
| `/api/webhook` | POST | Stripe `checkout.session.completed`, emails both sides. |

Each returns `503` with a plain-English reason when its keys are missing, which
is what the front end listens for before falling back.

## Running locally

```bash
npm install
npx vercel dev
```

Serving `index.html` with any static server also works, but the two API routes
will not respond, so the buttons will exercise their fallbacks instead.

## Editing rules

The film is locked. `claude.md` holds the project constitution: the brand
tokens, the frame contract, and the architectural invariants. `architecture/`
holds the pipeline SOP. Read those before touching `frames/`, `pipeline/`, or
the scrub engine at the bottom of `index.html`.

Everything a customer could act on (prices, locations, phone, email, partners,
booking links) is real and came from the business. Do not invent reviews,
ratings, session times, or guarantees.
