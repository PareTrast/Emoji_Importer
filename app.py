from flask import Flask, render_template, send_file
import emoji
import plistlib
import io
import sys
import os

# Use standard Flask convention, which automatically looks for a 'templates' folder.
app = Flask(__name__)

# Cache the mappings to avoid re-processing on every request
CACHED_MAPPINGS = None

def get_mappings():
    global CACHED_MAPPINGS
    if CACHED_MAPPINGS is not None:
        return CACHED_MAPPINGS

    print("Generating emoji mappings... (this may take a moment)", file=sys.stdout, flush=True)
    mappings = []
    
    # Handle different versions of the emoji library (v1 vs v2)
    if hasattr(emoji, 'EMOJI_DATA'):
        source_data = emoji.EMOJI_DATA # v2.0+
        is_v2 = True
    else:
        # Fallback for older versions
        source_data = getattr(emoji, 'UNICODE_EMOJI', {})
        if 'en' in source_data: source_data = source_data['en']
        is_v2 = False

    for char, data in source_data.items():
        # Extract name based on version
        if is_v2:
            if not isinstance(data, dict): continue
            raw_name = data.get('en', "")
        else:
            raw_name = data

        # clean the name (e.g. ":thumbs_up:" -> "thumbs up")
        clean_name = raw_name.replace(":","").strip().lower()
        
        if clean_name:
            # prefix with colon: "fire" becomes ":fire"
            shortcut = f":{clean_name}"
            mappings.append({"phrase": char, "shortcut": shortcut})
    
    print(f"Processing complete. Found {len(mappings)} emojis.", file=sys.stdout, flush=True)
    CACHED_MAPPINGS = mappings
    return mappings

@app.route('/')
def index():
    try:
        print("Request received for index.", file=sys.stdout, flush=True)
        # pass 10 examples to the frontend for the preview
        data = get_mappings()
        examples = data[:10] if data else []
        return render_template('index.html', examples=examples)
    except Exception as e:
        print(f"Error rendering index: {e}", file=sys.stdout, flush=True)
        return f"<h2>An error occurred:</h2><pre>{e}</pre>"

@app.route('/download/<platform>')
def download(platform):
    try:
        mappings = get_mappings()
        if platform == "ios":
            buffer = io.BytesIO()
            plistlib.dump(mappings, buffer)
            buffer.seek(0)
            return send_file(buffer, as_attachment=True, download_name="TypewiseEmojis.plist")
        else:
            output = "shortcut,phrase,locale\n"
            for m in mappings:
                output += f"{m['shortcut']},{m['phrase']},en\n"
            buffer = io.BytesIO(output.encode('utf-8'))
            return send_file(buffer, as_attachment=True, download_name="TypewiseEmojis.csv")
    except Exception as e:
        return f"Download error: {e}"
    
if __name__ == '__main__':
    print("Starting Flask server on http://127.0.0.1:5001", file=sys.stdout, flush=True)
    app.run(debug=True, port=5001)