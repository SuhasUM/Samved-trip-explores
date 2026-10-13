# Samved Trip Explores

A premium, responsive Karnataka tourism website built with Vite and plain JavaScript.

## Run locally

```bash
npm install
npm run dev
```

Open the local URL Vite prints in the terminal. For a production check, use `npm run build`.

## Enquiry delivery setup

The contact form includes its Web3Forms `access_key` in a hidden field in `main.js`. Form submissions are posted from the browser to Web3Forms, then WhatsApp opens with the same trip details prefilled; the visitor taps Send there to share them. The access key is a public form identifier intended for client-side use.

## Notes

- The supplied Samved logo is used in the site header, footer, favicon, and Apple touch icon.
- Destination and gallery photography is stored locally in `assets/destinations`; an internet connection is needed for Google Fonts.
