import gradio as gr
import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from threading import Thread

# FastAPI Backend Setup
app = FastAPI()

# Allow Gradio to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Operation(BaseModel):
    operation: str
    number1: float
    number2: float = None  # Optional for single-operand operations

@app.post("/calculate")
async def calculate(operation: Operation):
    try:
        if operation.operation == "add":
            return {"result": operation.number1 + operation.number2}
        elif operation.operation == "subtract":
            return {"result": operation.number1 - operation.number2}
        elif operation.operation == "multiply":
            return {"result": operation.number1 * operation.number2}
        elif operation.operation == "divide":
            if operation.number2 == 0:
                raise HTTPException(status_code=400, detail="Division by zero is not allowed.")
            return {"result": operation.number1 / operation.number2}
        else:
            raise HTTPException(status_code=400, detail="Invalid operation.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Gradio Frontend Setup
def calculator(expression):
    try:
        # Check if there's an operator in the expression
        if "÷" in expression:
            number1, number2 = expression.split("÷")
            response = requests.post(
                "http://0.0.0.0:8000/calculate",
                json={"operation": "divide", "number1": float(number1), "number2": float(number2)},
            )
        elif "×" in expression:
            number1, number2 = expression.split("×")
            response = requests.post(
                "http://0.0.0.0:8000/calculate",
                json={"operation": "multiply", "number1": float(number1), "number2": float(number2)},
            )
        elif "+" in expression:
            number1, number2 = expression.split("+")
            response = requests.post(
                "http://0.0.0.0:8000/calculate",
                json={"operation": "add", "number1": float(number1), "number2": float(number2)},
            )
        elif "-" in expression:
            number1, number2 = expression.split("-")
            response = requests.post(
                "http://0.0.0.0:8000/calculate",
                json={"operation": "subtract", "number1": float(number1), "number2": float(number2)},
            )
        else:
            # If no operator, return the number itself as the result
            return expression.strip()

        if response.status_code == 200:
            return str(response.json()["result"])  # Ensure result is a string
        else:
            return response.json()["detail"]
    except Exception as e:
        return str(e)

# Create Gradio Interface
def create_interface():
    with gr.Blocks() as demo:
        gr.Markdown("## 100x Calculator")

        display_expression = gr.Textbox(label="Enter Expression", value="", interactive=False)
        result = gr.State(value="")  # Store the last result in a state
        reset_next = gr.State(value=False)  # Track if the next input should reset

        def update_expression(current_expression, button, result_value, reset_flag):
            if reset_flag and button not in ["+", "-", "×", "÷"]:
                # Reset if an operation was just completed and the next input is not an operator
                current_expression = ""
                reset_flag = False
            
            if button in ["+", "-", "×", "÷"]:
                if current_expression == "":
                    current_expression = result_value  # Use the result if starting a new expression
                reset_flag = False  # Ensure we don't reset on the next number input
                return current_expression + button, result_value, reset_flag
            elif button == "=":
                # If no operator is found, return the current expression as the result
                result_value = calculator(current_expression)
                return result_value, result_value, True  # Show result and set flag to reset next input
            elif button == "AC":
                return "", "", False  # Clear everything
            else:
                return current_expression + button, result_value, reset_flag

        # Proper Grid Layout for Buttons with swapped "AC" and "=" positions
        button_rows = [
            ["7", "8", "9", "÷"],
            ["4", "5", "6", "×"],
            ["1", "2", "3", "-"],
            ["0", ".", "AC", "+"],  # AC button swapped with "="
            ["="],  # "=" button now on its own row
        ]

        for row in button_rows:
            with gr.Row():
                for button in row:
                    gr.Button(button).click(
                        update_expression,
                        inputs=[display_expression, gr.State(value=button), result, reset_next],
                        outputs=[display_expression, result, reset_next],
                    )

    return demo

demo = create_interface()

def run_gradio():
    demo.launch(server_name="0.0.0.0", server_port=7860)

# Run FastAPI and Gradio simultaneously
if __name__ == "__main__":
    thread = Thread(target=run_gradio)
    thread.start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
