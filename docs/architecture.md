# Architecture

The script loops over configured URLs, fetches each page and checks for one target string. A missing string adds the page to an alert list; HTTP failures return an unknown result. If the alert list is non-empty, a combined message is sent through Telegram.

No persistent alert state or deduplication is implemented. A future change could persist availability transitions and validate Telegram responses. Those are proposed improvements, not present features.
