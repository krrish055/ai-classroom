# Security

Do not file public GitHub issues that contain API keys, `.env` dumps, audio of real students, or Simli session tokens.

## Reporting

Email or message the maintainers privately. Include:

- Affected version / commit
- Impact (key leak, auth bypass, prompt injection that changes **spoken** text, etc.)
- Reproduction without secrets in the clear if possible

We will rotate exposed keys and patch before any disclosure.

## Policy for this repo

- `.env` is gitignored; only `.env.example` is committed
- Enable GitHub secret scanning and push protection on the remote
- Dependabot alerts should stay on
- Never log raw keys, tokens, or full audio
