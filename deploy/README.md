# deploy/

What is actually in this directory:

- **`pages.md`**, the DEFAULT: GitHub Pages static deploy (ADR-0055), driven by
  `.github/workflows/deploy-pages.yml`. This is the path SymLab uses.
- **`fasl-slug.service`** and **`domain.nginx`**, DORMANT templates for the VPS path, used ONLY if the
  `app/` backend is ever activated (an ADR-0002 trigger). SymLab does not need them: the site is static
  and the only computation at request time happens in the reader's browser. They are kept as a
  one-switch on-ramp; rename the slug and the domain when you activate.

This list used to name `setup.sh` and `update.sh` alongside them. Neither file has ever existed here.
A directory listing that names files that are not present is worse than no listing, because it sends a
reader looking for an on-ramp that was never built.
