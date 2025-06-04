import gradio as gr
import time
import os
import json


INTERVAL = 1

LOCAL_FILES = {
"RELEVANT_OBJECTS_3D": "outputs/3d_relevant_objects.gif",
"RELEVANT_OBJECTS_2D": "outputs/overlayed_masks_sam_and_graph_relevant_objects.png",
"RELEVANT_OBJECTS_TEXT": "outputs/relevant_objects.txt",
"RELEVANT_OBJECTS_TABLE": "outputs/table_relevant_objects.json",

"FINAL_ANSWER_3D": "outputs/3d_final_answer.gif",
"FINAL_ANSWER_2D": "outputs/overlayed_masks_sam_and_graph_final_answer.png",
"FINAL_ANSWER_TEXT": "outputs/final_answer.txt",
"FINAL_ANSWER_TABLE": "outputs/table_final_answer.json",
}
USER_QUERY = 'user_query.txt'
DUMMY_QUERY = 'dummies/query.txt'
DUMMY_GIF = "dummies/loading.gif"
DUMMY_TXT = "dummies/loading.txt"
DUMMY_TABLE = "dummies/table.json"
DUMMY_OUTPUTS = {
"USER_QUERY": DUMMY_QUERY,
"RELEVANT_OBJECTS_3D": DUMMY_GIF,
"RELEVANT_OBJECTS_2D": DUMMY_GIF,
"RELEVANT_OBJECTS_TEXT": DUMMY_TXT,
"RELEVANT_OBJECTS_TABLE": DUMMY_TABLE,
"FINAL_ANSWER_3D": DUMMY_GIF,
"FINAL_ANSWER_2D": DUMMY_GIF,
"FINAL_ANSWER_TEXT": DUMMY_TXT,
"FINAL_ANSWER_TABLE": DUMMY_TABLE,
}

def generate_html_table(json_data):
    rows = ""
    for row in json_data:
        color = row.get("color", "#ffffff")
        label = row.get("label", "N/A")
        rows += f"<tr style='background-color:{color};'>"
        rows += f"<td style='border: 1px solid #ccc; padding: 4px;'>{label}</td>"
        rows += "</tr>"

    html = f"""
    <div style='height:400px; overflow-y:auto; border:1px solid #ccc;'>
        <table style='width:100%; border-collapse: collapse;'>
            <tr><th>ID: Value</th></tr>
            {rows}
        </table>
    </div>
    """
    return html

def load_image_info(current_outputs):
    with open(current_outputs["USER_QUERY"], 'r') as f:
        user_query = f.read()
    user_query = f" ##  User query: {user_query}"

    with open(current_outputs["RELEVANT_OBJECTS_TEXT"], 'r') as f:
        relevant_text = f.read()

    with open(current_outputs["FINAL_ANSWER_TEXT"], 'r') as f:
        final_text = f.read()

    with open(current_outputs["RELEVANT_OBJECTS_TABLE"], 'r') as f:
        table1 = generate_html_table(json.load(f))

    with open(current_outputs["FINAL_ANSWER_TABLE"], 'r') as f:
        table2 = generate_html_table(json.load(f))

    return (
        current_outputs["RELEVANT_OBJECTS_3D"], table1, current_outputs["RELEVANT_OBJECTS_2D"],
        relevant_text,
        current_outputs["FINAL_ANSWER_3D"], table2, current_outputs["FINAL_ANSWER_2D"],
        final_text, relevant_text, user_query)

def get_local_file_timestamp(local_path):
    if os.path.exists(local_path):
        return int(os.path.getmtime(local_path))
    return None

def monitor_and_update():
    last_mtimes = {key: get_local_file_timestamp(path) for key, path in LOCAL_FILES.items()}
    query_mtimes = get_local_file_timestamp(USER_QUERY)
    yield load_image_info(DUMMY_OUTPUTS)
    while True:
        time.sleep(INTERVAL)
        if query_mtimes != get_local_file_timestamp(USER_QUERY):
            query_mtimes = get_local_file_timestamp(USER_QUERY)
            current_outputs = DUMMY_OUTPUTS
            current_outputs["USER_QUERY"] = USER_QUERY
            yield load_image_info(current_outputs)
            while True:
                updated = False
                break_out = True
                for key, path in LOCAL_FILES.items():
                    current_mtime = get_local_file_timestamp(path)
                    if current_mtime != last_mtimes[key]:
                        last_mtimes[key] = current_mtime
                        current_outputs[key] = path
                        updated = True
                    break_out &= (current_mtime != last_mtimes[key])
                if updated:
                    yield load_image_info(current_outputs)
                if break_out:
                    break

def demo():
    with gr.Blocks(fill_height=True) as interface:
        gr.Markdown("# BBQ Demo")
        markdown_display = gr.Markdown()
        with gr.Row():
            img_1_3d = gr.Image(width=400, height=400, format="gif", scale=2)
            with gr.Column(scale=1):
                table_1 = gr.HTML()
            img_1_2d = gr.Image(height=400, scale=3)
        desc1 = gr.Textbox(label="Target and anchor objects")

        with gr.Row():
            img_2_3d = gr.Image(width=400, height=400, format="gif", scale=2)
            with gr.Column():
                table_2 = gr.HTML()
            img_2_2d = gr.Image(height=400, scale=3)
        desc12 = gr.Textbox(label="Target and anchor objects")
        desc2 = gr.Textbox(label="Final answer")

        interface.load(monitor_and_update, None, [img_1_3d, table_1, img_1_2d, desc1, img_2_3d, table_2, img_2_2d, desc2, desc12, markdown_display])
    return interface

demo().launch(share=True)
