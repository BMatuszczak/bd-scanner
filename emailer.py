import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

from config import EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT


def score_color(score: int) -> str:
    """Return a color hex based on score."""
    if score >= 80:
        return "#1a7f37"  # dark green
    if score >= 60:
        return "#2da44e"  # green
    if score >= 40:
        return "#d29922"  # amber
    return "#cf222e"      # red


def score_badge(score: int) -> str:
    color = score_color(score)
    return (
        f'<span style="background:{color};color:#fff;'
        f'padding:3px 10px;border-radius:12px;font-weight:bold;'
        f'font-size:14px;">{score}</span>'
    )


def signal_tags(signals: list[str]) -> str:
    tag_style = (
        "display:inline-block;margin:2px 3px;padding:2px 8px;"
        "background:#eaf0fb;color:#1c3a6b;border-radius:10px;font-size:12px;"
    )
    return "".join(f'<span style="{tag_style}">{s}</span>' for s in signals)


def article_links(articles: list[dict]) -> str:
    items = []
    for a in articles[:3]:  # max 3 articles per company
        date_str = ""
        if a.get("published"):
            date_str = f' <span style="color:#888;font-size:11px;">({a["published"].strftime("%d %b")})</span>'
        items.append(
            f'<li style="margin:3px 0;">'
            f'<a href="{a["link"]}" style="color:#0969da;text-decoration:none;">{a["title"]}</a>'
            f'{date_str}</li>'
        )
    return "<ul style='margin:4px 0 0 0;padding-left:18px;'>" + "".join(items) + "</ul>"


def build_html(companies: list[dict]) -> str:
    today = datetime.now().strftime("%A, %d %B %Y")
    rows = ""

    for i, co in enumerate(companies):
        bg = "#ffffff" if i % 2 == 0 else "#f6f8fa"
        rows += f"""
        <tr style="background:{bg};vertical-align:top;">
            <td style="padding:12px 16px;font-size:18px;font-weight:600;color:#1f2328;width:30%;">
                {co['name']}
            </td>
            <td style="padding:12px 16px;text-align:center;width:10%;">
                {score_badge(co['score'])}
            </td>
            <td style="padding:12px 16px;width:20%;">
                {signal_tags(co['signals'])}
            </td>
            <td style="padding:12px 16px;width:40%;">
                {article_links(co['articles'])}
            </td>
        </tr>
        """

    if not companies:
        rows = """
        <tr><td colspan="4" style="padding:24px;text-align:center;color:#888;">
            No strong BD signals found today. Check back tomorrow.
        </td></tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 background:#f6f8fa;margin:0;padding:20px;">
        <div style="max-width:900px;margin:0 auto;">

            <!-- Header -->
            <div style="background:#1c3a6b;color:#fff;padding:24px 32px;
                        border-radius:10px 10px 0 0;">
                <h1 style="margin:0;font-size:22px;">
                    Latitude IT — BD Signal Report
                </h1>
                <p style="margin:6px 0 0 0;opacity:0.8;font-size:14px;">{today}</p>
            </div>

            <!-- Summary bar -->
            <div style="background:#fff;padding:16px 32px;border-left:1px solid #d0d7de;
                        border-right:1px solid #d0d7de;">
                <p style="margin:0;color:#57606a;font-size:14px;">
                    <strong>{len(companies)} companies</strong> identified with active BD signals in Australia.
                    Score reflects strength of hiring intent (max 100).
                </p>
            </div>

            <!-- Table -->
            <table style="width:100%;border-collapse:collapse;
                          border:1px solid #d0d7de;border-top:none;
                          border-radius:0 0 10px 10px;overflow:hidden;
                          background:#fff;">
                <thead>
                    <tr style="background:#f6f8fa;border-bottom:2px solid #d0d7de;">
                        <th style="padding:10px 16px;text-align:left;
                                   font-size:12px;color:#57606a;text-transform:uppercase;
                                   letter-spacing:.05em;">Company</th>
                        <th style="padding:10px 16px;text-align:center;
                                   font-size:12px;color:#57606a;text-transform:uppercase;
                                   letter-spacing:.05em;">Score</th>
                        <th style="padding:10px 16px;text-align:left;
                                   font-size:12px;color:#57606a;text-transform:uppercase;
                                   letter-spacing:.05em;">Signals</th>
                        <th style="padding:10px 16px;text-align:left;
                                   font-size:12px;color:#57606a;text-transform:uppercase;
                                   letter-spacing:.05em;">News</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>

            <!-- Footer -->
            <p style="text-align:center;color:#aaa;font-size:12px;margin-top:20px;">
                Powered by Latitude IT BD Scanner &bull; Signals from Google News AU
            </p>
        </div>
    </body>
    </html>
    """


def send_digest(companies: list[dict]):
    """Send the HTML digest email."""
    if not all([EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECIPIENT]):
        raise ValueError(
            "Missing email config. Check EMAIL_SENDER, EMAIL_PASSWORD, "
            "EMAIL_RECIPIENT in your .env file."
        )

    today = datetime.now().strftime("%d %b %Y")
    subject = f"BD Signal Report — {len(companies)} leads — {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Latitude IT BD Scanner <{EMAIL_SENDER}>"
    msg["To"] = EMAIL_RECIPIENT

    html_content = build_html(companies)
    msg.attach(MIMEText(html_content, "html"))

    print(f"[emailer] Sending digest to {EMAIL_RECIPIENT}...")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECIPIENT, msg.as_string())

    print(f"[emailer] Email sent successfully.")
