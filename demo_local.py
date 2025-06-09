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

def generate_html_objects_table(json_data):
    rows = ""
    for row in json_data:
        label = row.get("label", "N/A")
        obj_type = row.get("type", "others").capitalize()
        span_html = f'<span class="{obj_type}" style="display: block; width: 100%;">{label}</span>'
        rows += f"<tr><td style='border: none; padding: 0px; margin 0px; width: 100%;'>{span_html}</td></tr>"

    html = f"""
    <div style='height:400px; overflow-y:auto; border:1px solid #ccc;'>
        <table style='width:100%; border-collapse: collapse; table-layout: fixed;'>
            <tr><th style='width:100%; text-align: left;'>ID: Value</th></tr>
            {rows}
        </table>
    </div>
    """
    return html

def generate_html_relations_table(json_data):
    rows = ""
    for row in json_data:
        sub = row.get("sub", "N/A")
        obj = row.get("obj", "N/A")
        rel = row.get("rel", "N/A")

        # Составляем HTML-строку
        sub_html = f'<span class="Targets">{sub}</span>'
        obj_html = f'<span class="Anchors">{obj}</span>'
        rel_html = f'<span class="explanation-box">{rel}</span>'

        # Формируем одну ячейку таблицы с двумя строками: "sub <-> obj" и "rel"
        cell_html = f"""
            <div style="display: flex; justify-content: start; gap: 1px;">
                {sub_html}{rel_html}{obj_html}
            </div>
        """

        rows += f"<tr><td style='border: none; padding: 0px; margin: 0px; width: 100%;'>{cell_html}</td></tr>"

    html = f"""
    <div style='height:400px; overflow-y:auto; border:1px solid #ccc;'>
        <table style='width:100%; border-collapse: collapse; table-layout: fixed;'>
            <tr><th style='width:100%; text-align: left;'>sub / relation / obj</th></tr>
            {rows}
        </table>
    </div>
    """
    return html

def format_target_and_anchors(text): #new_func
    """Извлекаем Target and anchor objects"""
    
    if '{' in text and '}' in text:
        json_part = text[text.find('{'):text.find('}')+1]
        try:
            data = json.loads(json_part.replace("'", '"'))
            referred_objects = data['referred objects']
            anchors = data['anchors']
        except:
            pass 

    for i in range(len(referred_objects)):
        obj, id = referred_objects[i].split(" with id ")
        referred_objects[i] = f"{id}: {obj}"

    for i in range(len(anchors)):
        obj, id = anchors[i].split(" with id ")
        anchors[i] = f"{id}: {obj}"

    return referred_objects, anchors

def format_final_answer(text): #new_func
    """Форматирует поле Final answer"""
    print("text: ", text)
    if '{' in text and '}' in text:
        json_part = text[text.find('{'):text.find('}')+1]
        print("json_part: ", json_part)
        try:
            data = json.loads(json_part)
            explanation = data['explanation']
            id = data['id']
        except Exception as e:
            print("error: ", e)
            pass

    select = f"I select the object with id {id}"
    return [select, explanation]

def create_objects_html(title, list_obj1, list_obj2, name_list1, name_list2): #new func
    """Создает HTML-блок с заголовком, targets и anchors"""
    list_obj1_html = " ".join([f'<span class="{name_list1}" style="margin-right: 8px;">{item}</span>' for item in list_obj1])
    list_obj2_html = " ".join([f'<span class="{name_list2}" style="margin-right: 8px;">{item}</span>' for item in list_obj2])
    
    return f"""
    <div class="objects-container">
        <h3 style="margin-bottom: 15px;">{title}</h3>
        <div class="section-title">{name_list1}:</div>
        <div>{list_obj1_html}</div>
        <div class="section-title">{name_list2}:</div>
        <div>{list_obj2_html}</div>
    </div>
    """

def create_answer_html(title, list_obj):
    """Создает HTML-блок ответа в едином стиле с create_objects_html"""
    return f"""
    <div class="objects-container">
        <h3 style="margin-bottom: 15px;">{title}</h3>
        <div class="section-title">Selected object and explanation:</div>
        <div class="object-pair">
            <span class="id-box" style="margin-right: 8px;">{list_obj[0]}</span>
            <span class="explanation-box">{list_obj[1]}</span>
        </div>
    </div>
    """

def load_image_info(current_outputs):
    with open(current_outputs["USER_QUERY"], 'r') as f:
        user_query = f.read()
    user_query = f" ##  User query: {user_query}"

    with open(current_outputs["RELEVANT_OBJECTS_TABLE"], 'r') as f:
        json1 = json.load(f)
        obj_table1 = generate_html_objects_table(json1['objects'])
        rel_table1 = generate_html_relations_table(json1['relations'])

    with open(current_outputs["FINAL_ANSWER_TABLE"], 'r') as f:
        json2 = json.load(f)
        obj_table2 = generate_html_objects_table(json2['objects'])
        rel_table2 = generate_html_relations_table(json2['relations'])

    with open(current_outputs["RELEVANT_OBJECTS_TEXT"], 'r') as f:
        #relevant_text = f.read()
        targets, anchors = format_target_and_anchors(f.read()) #modified string

    with open(current_outputs["FINAL_ANSWER_TEXT"], 'r') as f:
        #final_text = f.read()
        answer = format_final_answer(f.read()) #modified string
        answer[0] = (next((item for item in json2["objects"] if item.get("type") == "targets"), {'label': 'Loading...'}))['label']

    if current_outputs["FINAL_ANSWER_3D"] != DUMMY_OUTPUTS["FINAL_ANSWER_3D"]:
        # Final stage
        return (
            current_outputs["FINAL_ANSWER_3D"],
            obj_table2, rel_table2,
            current_outputs["FINAL_ANSWER_2D"],
            create_objects_html("Target and anchors (deductive stage 1)", targets, anchors, "Targets", "Anchors"), #modified string
            create_answer_html("Final answer (deductive stage 2)", answer), #modified string
            user_query
        )
    else:
        # Stage 1
        return (
            current_outputs["RELEVANT_OBJECTS_3D"],
            obj_table1, rel_table1,
            current_outputs["RELEVANT_OBJECTS_2D"],
            create_objects_html("Target and anchors (deductive stage 1)", targets, anchors, "Targets", "Anchors"), #modified string
            create_answer_html("Final answer (deductive stage 2)", answer), #modified string
            user_query
        )

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
            current_outputs = DUMMY_OUTPUTS.copy()
            current_outputs["USER_QUERY"] = USER_QUERY
            yield load_image_info(current_outputs)
            break_out = set()
            while True:
                updated = False
                time.sleep(INTERVAL/2)
                for key, path in LOCAL_FILES.items():
                    current_mtime = get_local_file_timestamp(path)
                    if current_mtime != last_mtimes[key]:
                        last_mtimes[key] = current_mtime
                        current_outputs[key] = path
                        updated = True
                        break_out.add(path)
                if len(break_out) == len(LOCAL_FILES):
                    break
                if updated:
                    yield load_image_info(current_outputs)
            yield load_image_info(current_outputs)

with open("demo_css.txt", "r") as f:
    css = f.read()

def demo():
    with gr.Blocks(css=css, fill_height=True) as interface:
        gr.Markdown("# BBQ Demo")
        markdown_display = gr.Markdown()
        with gr.Row():
            img_1_3d = gr.Image(width=400, height=400, format="gif", scale=2)
            with gr.Column(scale=1):
                objects_table = gr.HTML()
            with gr.Column(scale=1):
                relations_table = gr.HTML()
            img_1_2d = gr.Image(height=400, scale=3)
        objects_section_1 = gr.HTML()
        objects_section_2 = gr.HTML()

        interface.load(monitor_and_update, None, [img_1_3d, objects_table, relations_table, img_1_2d, objects_section_1, objects_section_2, markdown_display])
    return interface

demo().launch(share=True)
