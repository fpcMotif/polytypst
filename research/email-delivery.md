# Email delivery from Convex or Cloudflare

Ticket: devv-568z. Researched 2026-10-17 against first-party docs. Prices and limits change, so re-check the linked pages before you commit to a plan.

## Answer

Use Resend, called from Convex through the official `@convex-dev/resend` component. Resend is the only provider here with a first-party Convex component, and Convex Auth uses Resend as its documented magic-link example. One Resend account and one verified domain can therefore serve both the "your Edition is ready" email and magic-link sign-in. The free plan (3,000 emails per month, 100 per day) covers an invite-only app. For download links, store Editions in R2 through the `@convex-dev/r2` component and return presigned URLs with `expiresIn`. If Editions stay in Convex file storage, serve them from an HTTP action that checks a signed, expiring token, because `ctx.storage.getUrl` URLs do not expire.

Cloudflare Email Service is the cheapest at volume. It is in beta, needs Workers Paid for arbitrary recipients, and has no Convex integration. Postmark has a 100-email free tier and no Convex component.

## Context in this repo

- The web app deploys to Cloudflare Workers (`web/wrangler.jsonc`, script `deploy:cf`).
- The backend is Convex (`web/convex/`, `convex@^1.47.0`). It has no auth, no components, and no `convex.config.ts` yet.
- The email trigger ("Edition is ready") fires when a Convex job finishes. A Convex action can call any HTTP API. A Workers `send_email` binding is reachable only from code that runs in the Worker.

## Provider comparison

| | Resend | Postmark | Cloudflare Email Service |
|---|---|---|---|
| Free tier | 3,000/month, 100/day, 3 domains, 30-day log retention | 100/month, no expiry | No outbound to arbitrary recipients on Workers Free |
| Entry paid | Pro $20/month: 50,000/month, no daily cap, $0.90 per 1,000 extra | Basic $15/month: 10,000/month, $1.80 per 1,000 extra | Workers Paid: 3,000/month included, $0.35 per 1,000 extra |
| Rate limit | 10 requests/second per team, same on all plans | Not checked | Conservative daily quota for new accounts, numbers not published |
| Domain setup | Any DNS. MX + SPF TXT on `send`, DKIM TXT on `resend._domainkey`. Cloudflare one-click via Domain Connect | Domain must be verified. Before account approval, sends go only to your verified domains | Domain must use Cloudflare DNS. Onboarding adds MX, SPF, DKIM on `cf-bounce`, and `_dmarc` |
| Status | GA | GA | Email Sending is beta |
| Convex integration | Official component `@convex-dev/resend` | None. Call its HTTP API from an action | None. Call the REST API from an action with a Cloudflare API token |
| Magic-link sign-in | Convex Auth example provider (`@auth/core/providers/resend`) | Custom Auth.js email provider | Custom Auth.js email provider |

Sources: [Resend pricing](https://resend.com/pricing), [Resend API rate limit](https://resend.com/docs/api-reference/introduction), [Resend Cloudflare DNS guide](https://resend.com/docs/knowledge-base/cloudflare), [Resend domains](https://resend.com/docs/dashboard/domains/introduction), [Postmark pricing](https://postmarkapp.com/pricing), [Postmark account approval](https://postmarkapp.com/support/article/1084-how-does-the-account-approval-process-work), [Cloudflare Email Service overview](https://developers.cloudflare.com/email-service/), [pricing](https://developers.cloudflare.com/email-service/platform/pricing/), [limits](https://developers.cloudflare.com/email-service/platform/limits/), [send emails](https://developers.cloudflare.com/email-service/get-started/send-emails/).

### Resend details

- Resend recommends sending from a subdomain such as `updates.example.com` instead of the root domain ([domains](https://resend.com/docs/dashboard/domains/introduction)).
- On Cloudflare DNS, set the DKIM record to "DNS Only" ([Cloudflare guide](https://resend.com/docs/knowledge-base/cloudflare)).

### Cloudflare Email Service details

- Three send paths exist: the Workers `send_email` binding (`env.EMAIL.send({ to, from, subject, html, text })`), the REST API `POST https://api.cloudflare.com/client/v4/accounts/{account_id}/email/sending/send` with a Bearer token, and SMTP ([send emails](https://developers.cloudflare.com/email-service/get-started/send-emails/)).
- Limits: 50 recipients per email, 5 MiB per message. Sends to verified destination addresses are free and do not count toward quota ([limits](https://developers.cloudflare.com/email-service/platform/limits/), [pricing](https://developers.cloudflare.com/email-service/platform/pricing/)).
- From Convex you would call the REST API and store a Cloudflare API token as a Convex env var. You would build retries, idempotency, and status tracking yourself.

## Convex Resend component

Source: [get-convex/resend README](https://github.com/get-convex/resend), [component page](https://www.convex.dev/components/resend).

1. Install `@convex-dev/resend` and register it with `app.use(resend)` in `convex/convex.config.ts`.
2. Set `RESEND_API_KEY` in the Convex deployment. Set `RESEND_WEBHOOK_SECRET` for delivery events.
3. Construct the client with `testMode: false` for real recipients. `testMode` defaults to `true` and only delivers to addresses such as `delivered@resend.dev`.
4. Call `resend.sendEmail(ctx, { from, to, subject, html })` from a mutation or action. It returns an `EmailId`.
5. Pass `idempotencyKey` (for example the Edition id) so a retried job does not send twice.

What the component adds over a raw `fetch`:

- A durable queue on Convex workpools that retries temporary failures.
- Automatic batching through Resend's `/emails/batch` endpoint, within Resend rate limits.
- Status per email through `resend.status(ctx, emailId)`, fed by a webhook route that calls `resend.handleResendEventWebhook(ctx, req)` in `convex/http.ts`. An `onEmailEvent` callback can react to bounces.
- `resend.cancelEmail` before the email reaches Resend.
- `cleanupOldEmails` and `cleanupAbandonedEmails`, which you schedule from a cron. Without them, finalized email rows stay forever.

## Magic-link sign-in for an invite-only app

Two Convex-native auth libraries can send magic links. Both accept any email sender, so the provider choice above does not lock the auth choice.

### Convex Auth

- Add `Resend` from `@auth/core/providers/resend` to `providers` in `convex/auth.ts`. Set `AUTH_RESEND_KEY` and `SITE_URL`. The client calls `signIn("resend", formData)` ([Convex Auth magic links](https://labs.convex.dev/auth/config/email)).
- This built-in provider calls the Resend API directly. It does not use the Resend component queue.
- For another sender, build a custom provider with `Email` from `@convex-dev/auth/providers/Email` and your own `sendVerificationRequest` ([Email provider reference](https://labs.convex.dev/auth/api_reference/providers/Email)).
- Auth.js magic links last 24 hours by default ([Auth.js email](https://authjs.dev/getting-started/authentication/email)). The Convex Auth reference lists `maxAge` but does not state its default ([server reference](https://labs.convex.dev/auth/api_reference/server)).
- Invite-only: Convex Auth has no allowlist switch. The `createOrUpdateUser` callback replaces user creation, so it can look up an `invites` table before it inserts a user ([advanced](https://labs.convex.dev/auth/advanced)). The docs do not say whether a throw there rejects sign-in. `beforeSessionCreation` is documented as "Throw an error to reject the sign-in" ([server reference](https://labs.convex.dev/auth/api_reference/server)). A second guard in `sendVerificationRequest` can skip mail to uninvited addresses.

### Better Auth

- Convex supports Better Auth through a component ([Convex + Better Auth](https://labs.convex.dev/better-auth)).
- The magic-link plugin takes `sendMagicLink({ email, token, url, metadata }, ctx)`. Links expire after 300 seconds by default. `disableSignUp: true` blocks account creation through magic links, which fits an invite-only app ([magic-link plugin](https://www.better-auth.com/docs/plugins/magic-link)).

## Expiring download links

### Convex file storage

- `ctx.storage.getUrl` returns a bearer URL. The docs give no expiry, and the only revocation is deleting the file ([serving files](https://docs.convex.dev/file-storage/serve-files)).
- For access control, the docs say to serve bytes from an HTTP action that "should authenticate the request and check that the caller can access the file". They also say "Do not use the storage ID as the only access check."
- HTTP action responses are limited to 100 MiB. Large Editions do not fit this path.
- To build an expiring link here, put a token in the URL that is an HMAC over `editionId` and `expiresAt`, keyed by a Convex env var. The HTTP action checks the HMAC and the clock, then streams the blob. Alternatively, store a random token with `expiresAt` in a table and look it up. This is project code, not a Convex feature.

### Cloudflare R2

- R2 presigned URLs last from 1 second to 7 days (604,800 seconds). They support `GET`, `HEAD`, `PUT`, and `DELETE`. They work only on `<ACCOUNT_ID>.r2.cloudflarestorage.com`, not on custom domains ([R2 presigned URLs](https://developers.cloudflare.com/r2/api/s3/presigned-urls/)).
- The `@convex-dev/r2` component wraps this. `r2.getUrl(key, { expiresIn })` returns a signed URL, with a default of 900 seconds. `r2.store` uploads from an action. It needs `R2_TOKEN`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`, and `R2_BUCKET` ([get-convex/r2](https://github.com/get-convex/r2)).
- The Convex docs point to this component "If you need file URLs that automatically expire after some time" ([serving files](https://docs.convex.dev/file-storage/serve-files)).
- An email link that must outlive 7 days cannot be a raw presigned URL. Link the email to an app route such as `/editions/{id}/download`. That route checks the session, then redirects to a fresh short-lived presigned URL. This also keeps the link working after sign-in.

## Recommendation

1. Verify a sending subdomain in Resend through Cloudflare Domain Connect.
2. Add `@convex-dev/resend` and send "Edition is ready" from the Convex job, with the Edition id as `idempotencyKey`.
3. Use the same Resend domain for magic links. Convex Auth with the Resend provider is the shortest path. Better Auth gives a ready `disableSignUp` switch for invite-only.
4. Email an app download route, not a storage URL. Behind it, issue an R2 presigned URL for 15 minutes to 1 hour, or stream from Convex storage when Editions stay under 100 MiB.
5. Move to Resend Pro when daily sends pass 100. Revisit Cloudflare Email Service when it leaves beta and volume makes the $0.35 per 1,000 rate matter.

## Open questions

- Where do Editions live, Convex storage or R2, and how large do they get? Above 100 MiB, Convex HTTP actions cannot serve them.
- Which domain sends mail, and is its DNS on Cloudflare? Cloudflare Email Service requires Cloudflare DNS.
- Convex Auth or Better Auth? This decides how invite-only is enforced and how long magic links last.
- Does a throw in Convex Auth `createOrUpdateUser` reject sign-in? The docs do not say. Test it before relying on it.
- Should download links in email expire, or should they require sign-in? The second avoids the 7-day presigned URL limit.
