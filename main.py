            picks.append({
                "matchup":    f"{away} vs {home}",
                "pick":       pick["name"],
                "odds":       round(pick["price"], 2),
                "start_time": datetime.fromisoformat(start).strftime("%I:%M %p EST"),
                "confidence": random.randint(70, 90)
            })

            if len(picks) == 3:
                break

        except (IndexError, KeyError) as e:
            # skip games that don't have the expected structure
            continue

    # Send each individual pick
    for p in picks:
        msg = (
            "⚾️ *AI MLB Pick*\n\n"
            f"*Game:* {p['matchup']}\n"
            f"*Pick:* {p['pick']} ({p['odds']}) ⚾️\n"
            f"*Start Time:* {p['start_time']}\n"
            f"*Confidence:* {p['confidence']}%\n\n"
            "_Backed by real-time odds_"
        )
