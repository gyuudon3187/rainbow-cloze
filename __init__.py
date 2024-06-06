from aqt.qt import *
from aqt.editor import Editor
from anki.hooks import addHook, wrap

previously_colored_text = {}

def setup_shortcut(editor):
    """
    Init function.
    Set up shortcuts for applying different colors to cloze deletions and selected text.

    Parameters:
        editor (Editor): The Anki editor instance.
    """
    for i in range(1, 9):
        shortcut = QShortcut(QKeySequence(f"Ctrl+{i}"), editor.parentWindow)
        shortcut.activated.connect(lambda i=i: process_selection(editor, i))

def process_selection(editor, num):
    """
    Main function.
    Apply color to cloze deletions and the selected text in the editor.

    Parameters:
        editor (Editor): The Anki editor instance.
        num (int): The number corresponding to a specific cloze deletion & the color to apply.
    """
    selected_text = get_selected_text(editor)

    if not selected_text:
        return

    text, back_extra = get_editor_fields(editor)
    color = get_color(num)
    cloze_id = f'c{num}'

    if cloze_id in previously_colored_text:
        text, back_extra = reset(text, back_extra, cloze_id)
    
    text, back_extra = apply_color(text, back_extra, selected_text, color, cloze_id)
    previously_colored_text[cloze_id] = { "text": selected_text, "color": color }

    update_fields(editor, text, back_extra)

def apply_color(text, back_extra, selected_text, color, cloze_id):
    """
    Helper function.
    Apply color to the selected text and cloze deletions.

    Parameters:
        text (str): The Text field content, i.e. the front of the card.
        back_extra (str): The Back Extra field content, i.e. the back of the card.
        selected_text (str): The text selected by the user.
        color (str): The hex color code to apply.
        cloze_id (str): The cloze ID corresponding to the selected color.
    
    Returns:
        Tuple[str, str]: The updated Text (front) and Back Extra (back) fields' content.
    """
    if selected_text in text:
        text = apply_color_to_text(selected_text, color, text)
    elif selected_text in back_extra:
        back_extra = apply_color_to_text(selected_text, color, back_extra)

    text = apply_color_to_cloze(text, cloze_id, color)

    return text, back_extra

def apply_color_to_text(selected_text, color, text):
    """
    Helper function.
    Apply color to the selected text.

    Parameters:
        selected_text (str): The text to color.
        color (str): The color to apply.
        text (str): The Text (front) field content.
    
    Returns:
        str: The updated Text (front) field content.
    """
    return text.replace(selected_text, f'<span style="color:{color}">{selected_text}</span>')

def apply_color_to_cloze(text, cloze_id, color):
    """
    Helper function.
    Apply color to cloze deletions.

    Parameters:
        text (str): The Text (front) field content.
        cloze_id (str): The cloze ID corresponding to the selected color.
        color (str): The color to apply.
    
    Returns:
        str: The updated Text (front) field content.
    """
    import re
    pattern = r'\{\{' + cloze_id + r'::(.*?)\}\}'

    def helper(match):
        clozed_phrase = match.group(1)
        return f'{{{{{cloze_id}::<span style="color: {color}">{clozed_phrase}</span>}}}}'

    return re.sub(pattern, helper, text)

def get_color(num):
    """
    Helper function.
    Get the color corresponding to the given number.

    Parameters:
        num (int): The number corresponding to the color.
    
    Returns:
        str: The color code.
    """
    colors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF', '#FFFF00', '#FFA500', '#800080', '#008000']
    return colors[num-1]

def get_editor_fields(editor):
    """
    Helper function.
    Get the Text (front) and Back Extra (back) fields from the editor.

    Parameters:
        editor (Editor): The Anki editor instance.
    
    Returns:
        Tuple[str, str]: The Text (front) and Back extra (back) fields.
    """
    return editor.note.fields[0], editor.note.fields[1]

def get_selected_text(editor):
    """
    Helper function.
    Get the currently selected text in the editor, stripped of adjacent blank spaces.

    Parameters:
        editor (Editor): The Anki editor instance.
    
    Returns:
        str: The selected text.
    """
    return editor.web.selectedText().strip()

def reset(text, back_extra, cloze_id):
    """
    Helper function.
    Reset the previously colored text to its original state.

    Parameters:
        text (str): The Text (front) field content.
        back_extra (str): The Back Extra (back) field content.
        cloze_id (str): The cloze ID to reset.
    
    Returns:
        Tuple[str, str]: The updated Text (front) and Back Extra (back) fields' content.
    """
    colored_text_info = previously_colored_text[cloze_id]

    if colored_text_info["text"] in text:
        text = reset_previous_color(colored_text_info, text)
    elif colored_text_info["text"] in back_extra:
        back_extra = reset_previous_color(colored_text_info, back_extra)
    
    return text, back_extra

def reset_previous_color(text_info, text):
    """
    Helper function.
    Reset the previously colored text to its original state in either the Text or Back Extra field.

    Parameters:
        text_info (Dict[str, Any]): The text and color of the previously colored text.
        text (str): Either the Text (front) or Back Extra (back) field content.
    
    Returns:
        str: The updated text content.
    """
    return text.replace(f'<span style="color:{text_info["color"]}">{text_info["text"]}</span>', text_info["text"])


def update_fields(editor, text, back_extra):
    """
    Helper function.
    Update the editor's note fields with the modified text and back_extra.

    Parameters:
        editor (Editor): The Anki editor instance.
        text (str): The Text (front) field content.
        back_extra (str): The Back Extra (back) field content.
    """
    editor.note.fields[0] = text
    editor.note.fields[1] = back_extra
    editor.loadNoteKeepingFocus()

def on_card_added():
    """
    Helper function.
    Clear the previously colored text when a new card is added.
    """
    global previously_colored_text
    previously_colored_text = {}

def on_editor_closed(editor):
    """
    Helper function.
    Clear the previously colored text when the editor is closed.
    """
    global previously_colored_text
    previously_colored_text = {}

addHook("afterAddNote", on_card_added)
addHook("editorDidClose", on_editor_closed)

Editor.setupShortcuts = wrap(Editor.setupShortcuts, setup_shortcut)