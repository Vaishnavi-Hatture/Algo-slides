import importlib
import json

from flask import Flask, render_template, request, redirect, url_for, flash

# module name has a hyphen, so import it dynamically
search_engine = importlib.import_module("search-engine")

app = Flask(__name__)
app.secret_key = "algo-slides-dev-key"  # only needed for flash() messages


def grouped_algorithms():
    """Algorithms bucketed by category, in CSV order, for the picker UI."""
    groups = {key: [] for key in search_engine.CATEGORIES}
    for key, algo in search_engine.ALGORITHMS.items():
        groups.setdefault(algo["category"], []).append((key, algo))
    return groups


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        categories=search_engine.CATEGORIES,
        groups=grouped_algorithms(),
    )


@app.route("/slides", methods=["POST"])
def show_slides():
    algo_key = request.form.get("algorithm", "linear")
    algo = search_engine.ALGORITHMS.get(algo_key)
    if algo is None:
        flash(f"Unknown algorithm '{algo_key}'.")
        return redirect(url_for("index"))

    raw_array = request.form.get("array", "")
    raw_target = request.form.get("target", "")
    raw_n = request.form.get("n", "")

    try:
        if algo["input"] == "n":
            if not raw_n.strip():
                raise ValueError("The limit (n) field is empty.")
            n = int(raw_n)
            display_arr = list(range(2, max(2, n) + 1))
            steps = algo["runner"](n)
            target = None
        else:
            arr = [int(x.strip()) for x in raw_array.split(",") if x.strip() != ""]
            if not arr:
                raise ValueError("The array field is empty or has no valid integers.")
            display_arr = sorted(arr) if algo["needs_sorted"] else arr

            if algo["input"] == "array_target":
                if not raw_target.strip():
                    raise ValueError("The target field is empty.")
                target = int(raw_target)
                steps = algo["runner"](display_arr, target)
            else:
                target = None
                steps = algo["runner"](display_arr)
    except ValueError as e:
        detail = str(e) if str(e) and not str(e).startswith("invalid literal") else \
            "Please enter comma-separated whole numbers only (e.g. 4, 12, 1, 9)."
        flash(f"Couldn't run {algo['label']}: {detail}")
        return redirect(url_for("index"))

    return render_template(
        "show_slides.html",
        algo_label=algo["label"],
        algo_key=algo_key,
        array=display_arr,
        target=target,
        steps=steps,
        steps_json=json.dumps(steps),
    )


if __name__ == "__main__":
    app.run(debug=True)
