import json

class Error:
    # Text and history will be appended to while 
    # correct_output will be set.
    text = []
    correct_output = None
    history = []

    def json():
        error_type = None
        if self.history and self.correct_output:
            error_type = "test_case"
        elif self.history and error_text:
            error_type = "user"
        else:
            error_type = "compiler"

        data = {"type": error_type,
                "history": self.history,
                "correct_text": self.error_text,
                "correct_output": self.correct_output}
        json_data = json.dumps(data)

        return json_data
