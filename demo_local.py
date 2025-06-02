import gradio as gr
import time
import os
import json

LOCAL_RELEVANT_OBJECTS_3D = "3d_relevant_objects.gif"
LOCAL_RELEVANT_OBJECTS_2D = "overlayed_masks_sam_and_graph_relevant_objects.png"
LOCAL_RELEVANT_OBJECTS_TEXT = "relevant_objects.txt"
LOCAL_RELEVANT_OBJECTS_TABLE = "table_relevant_objects.json"

LOCAL_FINAL_ANSWER_3D = "3d_final_answer.gif"
LOCAL_FINAL_ANSWER_2D = "overlayed_masks_sam_and_graph_final_answer.png"
LOCAL_FINAL_ANSWER_TEXT = "final_answer.txt"
LOCAL_FINAL_ANSWER_TABLE = "table_final_answer.json"

USER_QUERY = 'user_query.txt'

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

def load_image_info():
    with open(USER_QUERY, 'r') as f:
        user_query = f.read()
    user_query = f" ##  User query: {user_query}"

    with open(LOCAL_RELEVANT_OBJECTS_TEXT, 'r') as f:
        relevant_text = f.read()

    with open(LOCAL_FINAL_ANSWER_TEXT, 'r') as f:
        final_text = f.read()

    with open(LOCAL_RELEVANT_OBJECTS_TABLE, 'r') as f:
        table1 = generate_html_table(json.load(f))

    with open(LOCAL_FINAL_ANSWER_TABLE, 'r') as f:
        table2 = generate_html_table(json.load(f))

    return (
        LOCAL_RELEVANT_OBJECTS_3D, table1, LOCAL_RELEVANT_OBJECTS_2D,
        relevant_text,
        LOCAL_FINAL_ANSWER_3D, table2, LOCAL_FINAL_ANSWER_2D,
        final_text, relevant_text, user_query)

def monitor_and_update():
    last_mtime = None
    while True:
        time.sleep(2)  # Check for updates every 2 seconds
        if os.path.exists(LOCAL_FINAL_ANSWER_TEXT):
            mtime = os.path.getmtime(LOCAL_FINAL_ANSWER_TEXT)
            if last_mtime is None or mtime != last_mtime:
                last_mtime = mtime
                yield load_image_info()

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
