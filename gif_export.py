"""Render a small decision trace as an animated GIF."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def make_episode_gif(events: list[dict[str, object]], goal: tuple[int, int], output: Path) -> None:
    font = ImageFont.load_default()
    frames = []
    position = (0, 0)
    visited = {position}
    decisions = [event for event in events if event["type"] == "decision"]
    for event in [{"tool": "start"}] + decisions:
        if event.get("type") == "decision":
            position = tuple(event["coordinate"])
            visited.add(position)
        image = Image.new("RGB", (560, 620), "#f4efe5")
        draw = ImageDraw.Draw(image)
        draw.text((28, 24), "Prompt A", fill="#b66d25", font=font)
        draw.text((28, 48), f"move: {event['tool']}", fill="#25231f", font=font)
        draw.text((28, 70), f"agent: {position}   goal: {goal}", fill="#756e62", font=font)
        for row in range(5):
            for column in range(5):
                left, top = 28 + column * 100, 120 + row * 100
                color = "#d8c6a7" if (row, column) in visited else "#e8dfd1"
                if (row, column) == goal:
                    color = "#d99a55"
                if (row, column) == position:
                    color = "#477353" if (row, column) == goal else "#25231f"
                draw.rectangle((left, top, left + 94, top + 94), fill=color)
                text_color = "#fffaf1" if color in {"#25231f", "#477353"} else "#756e62"
                draw.text((left + 8, top + 8), f"{row},{column}", fill=text_color, font=font)
        frames.append(image)
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, save_all=True, append_images=frames[1:], duration=700, loop=0, optimize=True)
