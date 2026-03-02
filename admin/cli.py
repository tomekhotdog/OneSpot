"""OneSpot Admin CLI — Click + Rich terminal tool for platform management."""

import json

import click
import httpx
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

BANNER = """
╔═══════════════════════════════════════╗
║        ONESPOT ADMIN CONSOLE          ║
║     Parking Space Management Tool     ║
╚═══════════════════════════════════════╝
"""


@click.group()
@click.option("--url", required=True, help="Backend URL (e.g. http://localhost:8000)")
@click.option("--key", required=True, help="Admin API key")
@click.pass_context
def cli(ctx, url, key):
    """OneSpot Admin CLI — manage users, bookings, and credits."""
    console.print(BANNER, style="cyan")
    ctx.ensure_object(dict)
    ctx.obj["url"] = url.rstrip("/")
    ctx.obj["key"] = key


def _get(ctx, path):
    """Make an authenticated GET request to the admin API."""
    resp = httpx.get(
        f"{ctx.obj['url']}/api/admin{path}",
        headers={"X-Admin-Key": ctx.obj["key"]},
    )
    resp.raise_for_status()
    return resp.json()


def _patch(ctx, path, data):
    """Make an authenticated PATCH request to the admin API."""
    resp = httpx.patch(
        f"{ctx.obj['url']}/api/admin{path}",
        json=data,
        headers={"X-Admin-Key": ctx.obj["key"]},
    )
    resp.raise_for_status()
    return resp.json()


@cli.command()
@click.pass_context
def dashboard(ctx):
    """Show overview dashboard with key metrics."""
    stats = _get(ctx, "/stats")

    table = Table(title="Platform Overview", style="cyan", header_style="bold blue")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Total Users", str(stats["total_users"]))
    table.add_row("Total Owners", str(stats["total_owners"]))
    table.add_row("Total Bookings", str(stats["total_bookings"]))
    table.add_row("Active Bookings", str(stats["active_bookings"]))
    table.add_row("Cancelled Bookings", str(stats["cancelled_bookings"]))
    table.add_row(
        "Credits in Circulation",
        str(stats["total_credits_in_circulation"]),
    )
    table.add_row(
        "Most Active Bay",
        stats["most_active_bay"] or "N/A",
    )

    console.print(table)


@cli.command()
@click.pass_context
def users(ctx):
    """List all users with credit balances."""
    data = _get(ctx, "/users")

    table = Table(title="All Users", style="cyan", header_style="bold blue")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Name")
    table.add_column("Phone")
    table.add_column("Flat")
    table.add_column("Owner", justify="center")
    table.add_column("Bay")
    table.add_column("Credits", justify="right")

    for u in data["users"]:
        credits_val = u["credits"]
        credits_style = "green" if credits_val >= 24 else ("yellow" if credits_val > 0 else "red")
        table.add_row(
            u["id"][:12],
            u["name"],
            u["phone"],
            u["flat_number"],
            "Yes" if u["is_owner"] else "No",
            u.get("bay_number") or "-",
            Text(str(credits_val), style=credits_style),
        )

    console.print(table)


@cli.command()
@click.argument("user_id")
@click.pass_context
def user(ctx, user_id):
    """Show detailed info for a specific user."""
    data = _get(ctx, "/users")
    target = None
    for u in data["users"]:
        if u["id"] == user_id or u["id"].startswith(user_id):
            target = u
            break

    if not target:
        console.print(f"User not found: {user_id}", style="red")
        return

    panel_text = Text()
    panel_text.append(f"Name:       {target['name']}\n")
    panel_text.append(f"Phone:      {target['phone']}\n")
    panel_text.append(f"Flat:       {target['flat_number']}\n")
    panel_text.append(f"Owner:      {'Yes' if target['is_owner'] else 'No'}\n")
    panel_text.append(f"Bay:        {target.get('bay_number') or 'N/A'}\n")
    credits_val = target["credits"]
    credits_style = "green" if credits_val >= 24 else ("yellow" if credits_val > 0 else "red")
    panel_text.append("Credits:    ")
    panel_text.append(str(credits_val), style=credits_style)
    panel_text.append(f"\nCreated:    {target['created_at']}\n")
    panel_text.append(f"Last Login: {target['last_login']}")

    console.print(Panel(panel_text, title=f"User: {target['name']}", style="cyan"))


@cli.command()
@click.pass_context
def bookings(ctx):
    """List all bookings."""
    data = _get(ctx, "/bookings")

    table = Table(title="All Bookings", style="cyan", header_style="bold blue")
    table.add_column("ID", style="dim", max_width=12)
    table.add_column("Bay")
    table.add_column("Date")
    table.add_column("Time")
    table.add_column("Credits", justify="right")
    table.add_column("Status")

    for b in data["bookings"]:
        status = b["status"]
        status_style = "green" if status == "confirmed" else "red"
        table.add_row(
            b["id"][:12],
            b["bay_number"],
            b["date"],
            f"{b['start_hour']}:00-{b['end_hour']}:00",
            str(b["credits_charged"]),
            Text(status, style=status_style),
        )

    console.print(table)


@cli.command()
@click.argument("user_id")
@click.argument("amount", type=int)
@click.argument("reason")
@click.pass_context
def credits(ctx, user_id, amount, reason):
    """Adjust credits for a user. Positive to add, negative to deduct."""
    result = _patch(ctx, f"/users/{user_id}/credits", {"amount": amount, "reason": reason})
    style = "green" if amount >= 0 else "red"
    sign = "+" if amount >= 0 else ""
    console.print(
        f"Adjusted {result['name']}: {sign}{amount} credits "
        f"(new balance: {result['credits']})",
        style=style,
    )


@cli.command()
@click.pass_context
def stats(ctx):
    """Show detailed platform statistics."""
    stats_data = _get(ctx, "/stats")

    panel_text = Text()
    panel_text.append("Users\n", style="bold blue")
    panel_text.append(f"  Total:          {stats_data['total_users']}\n")
    panel_text.append(f"  Owners:         {stats_data['total_owners']}\n")
    panel_text.append(f"  Non-owners:     {stats_data['total_users'] - stats_data['total_owners']}\n\n")
    panel_text.append("Bookings\n", style="bold blue")
    panel_text.append(f"  Total:          {stats_data['total_bookings']}\n")
    panel_text.append(f"  Active:         {stats_data['active_bookings']}\n")
    panel_text.append(f"  Cancelled:      {stats_data['cancelled_bookings']}\n\n")
    panel_text.append("Credits\n", style="bold blue")
    panel_text.append(f"  In Circulation: {stats_data['total_credits_in_circulation']}\n\n")
    panel_text.append("Bays\n", style="bold blue")
    panel_text.append(f"  Most Active:    {stats_data['most_active_bay'] or 'N/A'}\n")

    console.print(Panel(panel_text, title="Platform Statistics", style="cyan"))


@cli.command()
@click.option("--output", "-o", default="state-export.json", help="Output file path")
@click.pass_context
def export(ctx, output):
    """Download full state.json to a local file."""
    data = _get(ctx, "/state")
    with open(output, "w") as f:
        json.dump(data, f, indent=2)
    console.print(f"Exported to {output}", style="green")


@cli.command()
@click.pass_context
def logs(ctx):
    """Show email message log."""
    state = _get(ctx, "/state")
    entries = state.get("email_log", [])

    if not entries:
        console.print("No email messages logged.", style="yellow")
        return

    table = Table(title="Email Message Log", style="cyan", header_style="bold blue")
    table.add_column("Time", style="dim")
    table.add_column("Recipient")
    table.add_column("Template")
    table.add_column("Status")
    table.add_column("Params", max_width=40)

    for entry in entries:
        table.add_row(
            entry.get("timestamp", "N/A"),
            entry["recipient"],
            entry["template"],
            entry.get("status", "N/A"),
            str(entry.get("params", {})),
        )

    console.print(table)


if __name__ == "__main__":
    cli()
