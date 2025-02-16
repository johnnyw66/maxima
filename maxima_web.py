from flask import Flask, request, jsonify, render_template_string, send_from_directory
import subprocess
import os
import sys
import datetime

sys.stdout.reconfigure(line_buffering=True)  # Python 3.7+

app = Flask(__name__)

# Directory to store generated plots
PLOTS_DIR = "/app/static/plots"
if not os.path.exists(PLOTS_DIR):
    os.makedirs(PLOTS_DIR)

# Serve plot files from the 'static/plots' directory
@app.route('/static/plots/<filename>')
def serve_plot(filename):
    return send_from_directory(PLOTS_DIR, filename)

# Welcome page with instructions and HTML form to submit plot commands
@app.route("/", methods=["GET"])
def welcome():
    return render_template_string("""
    <html>
        <head><title>plot2d Maxima Web Interface</title></head>
        <body>
            <h1>Maxima plot2d Web Interface</h1>
            <p>This is a simple web service to run plot2d Maxima commands and generate plots.</p>

            <h2>Enter a Maxima plot command:</h2>
            <p>Examples:<p>
            <p><b>sin(2*x), [x, -5, 5]</b></p>
            <p><b>[cos(x), sin(2*x)], [x, -5, 5]</b></p>
            <p><b>1/sqrt(2*%pi)*exp(-((x-0)^2)/2), [x, -5, 5]</p><b>
            <form action="/plot" method="post">
                <label for="command">Maxima Command:</label><br>
                <textarea id="command" name="command" rows="4" cols="50"></textarea><br><br>
                <input type="submit" value="Generate Plot">
            </form>

            {% if plot_url %}
                <h3>Generated Plot:</h3>
                <img src="{{ plot_url }}" alt="Generated Plot">
            {% endif %}

            <h2>To use the Maxima API with curl:</h2>
            <pre>
    curl -X POST http://localhost:5050/maxima -H "Content-Type: application/json" -d '{"command": "diff(sin(x),x);"}'
            </pre>
        </body>
    </html>
    """)
def plot_command_builder(command, plot_path):
    plot_cmd = f'"plot2d({command}, [gnuplot_term, png], [gnuplot_out_file,\\"{plot_path}\\"]);"'
    print(f"plot_command_builder: {plot_cmd}")
    return plot_cmd

def plot_command_builder_TEST(command, plot_path):
    plot_cmd = f'"sin(x);"'
    print(f"{plot_cmd}")
    return plot_cmd

# Endpoint to run Maxima commands and generate plots
@app.route("/plot", methods=["POST"])
def generate_plot():
    command = request.form.get("command", "")
    if not command:
        return render_template_string("<p>No command provided. Please enter a Maxima command.</p>")

    plot_filename = "plot.png"
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    plot_filename_ts = f'plot_{timestamp}.png'

    plot_path = os.path.join(PLOTS_DIR, plot_filename)
    plot_path_ts = os.path.join(PLOTS_DIR, plot_filename_ts)

    #print(f"PLOT COMMAND '{command}'")
    #print(f"PLOT PATH '{plot_path}'")

    # Run Maxima to generate the plot and save it to a file
    process_cmd = [
        "maxima", 
        "--very-quiet", 
        "--batch-string", 
        f"plot2d({command}, [gnuplot_term, png], [gnuplot_out_file,\"{plot_path_ts}\"]);"
    ]
    #print("PROCESS CMD ", process_cmd)
    result = subprocess.run(
       process_cmd,
        text=True, capture_output=True
    )
    #print("RESULT",result)
    if result.returncode != 0:
        return render_template_string("<p>Error generating plot: {{ result.stderr }}</p>", result=result)

    # Return the page with the plot image
    plot_url = f"/static/plots/{plot_filename_ts}"
    return render_template_string(f"""
        <h1>Plot Generated Successfully</h1>
        <img src="{plot_url}" alt="Generated Plot">
        <br><br>
        <p>filename: {plot_url}</P>
        <a href="/">Back to Home</a>
    """, plot_url=plot_url)

# Endpoint to run Maxima commands via POST request
@app.route("/maxima", methods=["POST"])
def run_maxima():
    command = request.json.get("command", "")
    if not command:
        return jsonify({"error": "No command provided"}), 400

    result = subprocess.run(["maxima", "--very-quiet"], input=command, 
                            text=True, capture_output=True)
    return jsonify({"output": result.stdout})


# Ensure the Flask app runs in the foreground
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
