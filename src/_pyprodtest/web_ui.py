import time
import json
from flask import Flask, request, render_template_string, Response
from threading import Thread
from queue import Queue, Empty

# Shared state
_data = {}            # question → answer
_pending = set()      # waiting for operator input
_report = []          # last report
_events = Queue()     # SSE queue
_measurements = {}    # test_name → [measurements]
_test_start_time = {} # test_name → epoch time when first measurement recorded

app = Flask(__name__)


@app.route("/")
def index():
    html = """<meta http-equiv="refresh" content="0;url=/ui">Redirecting to UI..."""
    return render_template_string(html)


@app.route("/ui")
def ui():
    html = """
    <h2>Operator Input</h2>
    <div id="questions"></div>

    <h3>Received responses:</h3>
    <pre id="responses"></pre>

    <h2>Measurements (vs Time)</h2>
    <canvas id="chart" width="700" height="250"></canvas>

    <h2>Latest Test Report</h2>
    <pre id="report"></pre>

    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
    const ctx = document.getElementById('chart');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
          datasets: [{
            label: 'Measurement Value',
            data: [],
            borderColor: 'blue',
            pointRadius: 0,
            borderWidth: 1
          }]
        },
        options: {
          animation: false,
          responsive: true,
          parsing: false,
          scales: {
            x: {
              type: 'linear',
              title: { display: true, text: 'Time (µs)' },
              ticks: { autoSkip: true, maxTicksLimit: 10 },
              min: 0
            },
            y: {
              beginAtZero: true,
              title: { display: true, text: 'Value' }
            }
          }
        }
    });

    const evt = new EventSource("/stream");
    evt.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === "input") {
            renderInputs(data.pending, data.responses);
        } else if (data.type === "report") {
            document.getElementById("report").textContent =
                JSON.stringify(data.report, null, 2);
        } else if (data.type === "measurement") {
        const m = data.data;
        chart.data.datasets[0].data.push({ x: m.time, y: m.value });

        // Dynamically adjust visible range to min/max
        const times = chart.data.datasets[0].data.map(p => p.x);
        const minT = Math.min(...times);
        const maxT = Math.max(...times);
        chart.options.scales.x.min = minT;
        chart.options.scales.x.max = maxT;

        chart.update('none');
        } else if (data.type === "reset") {
            chart.data.datasets[0].data = [];
            chart.options.scales.x.min = 0;
            chart.options.scales.x.max = undefined;
            chart.update();
        }
    };

    function renderInputs(pending, responses) {
        const container = document.getElementById("questions");
        const resp = document.getElementById("responses");
        container.innerHTML = "";
        resp.textContent = JSON.stringify(responses, null, 2);

        pending.forEach(q => {
            const form = document.createElement("div");
            form.innerHTML = `
                <b>${q}</b><br>
                <button onclick="submitAnswer('${q}', true)">Yes</button>
                <button onclick="submitAnswer('${q}', false)">No</button><hr>`;
            container.appendChild(form);
        });
    }

    function submitAnswer(question, answer) {
        fetch("/answer/" + encodeURIComponent(question), {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: "answer=" + (answer ? "yes" : "no")
        }).then(() => console.log("Answered:", question, answer));
    }
    </script>
    """
    return render_template_string(html)


@app.route("/stream")
def stream():
    def event_stream():
        yield from _snapshot_event()
        while True:
            try:
                data = _events.get(timeout=1)
                yield f"data: {json.dumps(data)}\n\n"
            except Empty:
                continue

    return Response(event_stream(), mimetype="text/event-stream")


@app.route("/answer/<path:question>", methods=["POST"])
def answer(question):
    _data[question] = request.form["answer"] == "yes"
    _pending.discard(question)
    _push_state()
    return ("", 204)  # no refresh


# ---- internal helpers ----
def _snapshot_event():
    yield f"data: {json.dumps({'type': 'input', 'pending': list(_pending), 'responses': _data})}\n\n"
    if _report:
        yield f"data: {json.dumps({'type': 'report', 'report': _report})}\n\n"


def _push_state():
    _events.put({"type": "input", "pending": list(_pending), "responses": _data})


# ---- public API ----
def get_input(question, poll_interval=0.5):
    if question not in _data:
        _pending.add(question)
        _push_state()
        print(f"Waiting for operator input: '{question}' (http://localhost:5000/ui)")
    while question not in _data:
        time.sleep(poll_interval)
    return _data[question]


def update_report(report_data):
    global _report
    _report = report_data
    _events.put({"type": "report", "report": report_data})


def update_measurement(test_name, name, value, unit):
    """Broadcast a new measurement to all connected clients with high-resolution time offset."""
    now = time.perf_counter_ns()
    if test_name not in _test_start_time:
        _test_start_time[test_name] = now
    t_offset_ns = now - _test_start_time[test_name]
    t_us = t_offset_ns / 1_000.0  # microseconds

    m = {
        "test": test_name,
        "name": name,
        "value": value,
        "unit": unit,
        "time": round(t_us, 3),
    }
    _measurements.setdefault(test_name, []).append(m)
    _events.put({"type": "measurement", "data": m})


def reset_measurements(test_name):
    """Reset measurements for a test before it starts."""
    _measurements[test_name] = []
    _test_start_time.clear()
    _events.put({"type": "reset", "test": test_name})


def start_ui():
    t = Thread(
        target=lambda: app.run(
            host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True
        )
    )
    t.daemon = True
    t.start()
