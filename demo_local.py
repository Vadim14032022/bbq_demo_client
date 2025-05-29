import gradio as gr
import time
import os

LOCAL_RELEVANT_OBJECTS_3D = "3d_relevant_objects.png"
LOCAL_RELEVANT_OBJECTS_2D = "overlayed_masks_sam_and_graph_relevant_objects.txt"
LOCAL_RELEVANT_OBJECTS_TEXT = "relevant_objects.png"

LOCAL_FINAL_ANSWER_3D = "3d_final_answer.png"
LOCAL_FINAL_ANSWER_2D = "overlayed_masks_sam_and_graph_final_answer.png"
LOCAL_FINAL_ANSWER_TEXT = "final_answer.txt"

USER_QUERY = 'user_query.txt'

def load_image_info():
    with open(USER_QUERY, 'r') as f:
        user_query = f.read()
    user_query = f" ##  User query: {user_query}"

    with open(LOCAL_RELEVANT_OBJECTS_TEXT, 'r') as f:
        relevant_text = f.read()

    with open(LOCAL_FINAL_ANSWER_TEXT, 'r') as f:
        final_text = f.read()

    return (
        LOCAL_RELEVANT_OBJECTS_3D, LOCAL_RELEVANT_OBJECTS_2D,
        relevant_text, LOCAL_FINAL_ANSWER_3D, 
        LOCAL_FINAL_ANSWER_2D, final_text, relevant_text, user_query)

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
            img_1_3d = gr.Image(width=400, height=400)
            img_1_2d = gr.Image(height=400)
        desc1 = gr.Textbox(label="Target and anchor objects")

        
        with gr.Row():
            img_2_3d = gr.Image(width=400, height=400)
            img_2_2d = gr.Image(height=400)
        desc12 = gr.Textbox(label="Target and anchor objects")
        desc2 = gr.Textbox(label="Final answer")
        interface.load(monitor_and_update, None, [img_1_3d, img_1_2d, desc1, img_2_3d, img_2_2d, desc2, desc12, markdown_display])
    return interface

demo().launch(share=True)
