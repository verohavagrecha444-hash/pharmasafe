from flask import Flask, render_template, request, redirect, url_for
import os

app = Flask(__name__)

# Home route → show index.html
@app.route("/")
def home():
    return render_template("index.html")

# Handle form submission
@app.route("/submit", methods=["POST"])
def submit():
    medicine_name = request.form.get("medicine_name")
    language = request.form.get("language")

    # If user uploaded a file, save it
    file = request.files.get("file")
    file_path = None
    if file and file.filename != "":
        upload_folder = os.path.join("uploads")
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, file.filename)
        file.save(file_path)

    # Just send data to results.html for now
    return render_template(
        "results.html",
        medicine_name=medicine_name,
        language=language,
        file_path=file_path
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
