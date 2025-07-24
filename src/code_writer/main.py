#!/usr/bin/env python
import json
import os
from pydantic import BaseModel, Field
from crewai import LLM
from crewai.flow.flow import Flow, listen, start, router, or_
from code_writer.crews.test_crew.test_crew import TestReviewCrew

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

# Define our flow state
class PythonCodeState(BaseModel):
    requirement: str = ""
    code: str = ""

class CodeWriterFlow(Flow[PythonCodeState]):
    """Flow for writing Python code based on user requirements"""

    @start()
    def get_user_input(self):
        """Get input from the user about the Python code requirement"""
        print("\n=== Write Your Python Code ===\n")

        # Get user input
        # self.state.requirement = input("What do you want to achieve with your Python code? ")
        self.state.requirement = "Write a Python function to calculate the Fibonacci sequence"

        print(f"\nGenerating Python code for: {self.state.requirement}...\n")
        return self.state

    @listen(get_user_input)
    def write_python_code(self, state):
        """Generate Python code based on the user's requirement"""
        print("Writing Python code...")

        llm = LLM(
            model="gemini/gemini-2.5-flash"
        )

        message = [
            {"role": "system", "content": "You are a Senior Python Programmer."},
            {"role": "user", "content": f"""
            Implement a Python function that {state.requirement}
            Make sure the function is efficient, well-documented, and follows best practices.
            Output Formatted as python code without '```'
            """}
        ]

        # Write the Python code using the LLM
        response = llm.call(message)

        self.state.code = response.strip()
        print(f"Generated code:\n{self.state.code}\n")

        return

    @listen(or_(write_python_code, "iterate"))
    def test_and_fix_code(self):
        print("Testing and fixing code...")

        result = TestReviewCrew().crew().kickoff(inputs={
            "requirement": self.state.requirement,
            "code": self.state.code
        })

        # parse the result(json)
        # result_data = result.json()
        data = parse_json(result.raw)
        print(f"Test results:\n{data}\n")
        data = json.loads(data)

        self.state.code = data["code"]
        return data["passed"]

    @router(test_and_fix_code)
    def review_result(self, ret):
        """Review the result of the code testing and fixing"""
        if ret == 'true':
            print("All tests passed! Code is ready.")
            return "terminate"
        else:
            print("Code needs fixing. Let's fix it.")
            return "iterate"

    @listen("terminate")
    def finalize_code(self):
        """Final step to indicate the code is ready"""
        print("Finalizing code...")
        with open('output/code.py', 'w') as f:
            f.write(f"{self.state.code}")
        print("Code written to output/code.py")

def parse_json(raw_data):
    """split json data from the raw string, according to the regular expression(```json\n(.*?)\n```), and return the parsed json data"""
    import re
    match = re.search(r'```json\n(.*?)\n```', raw_data, re.DOTALL)
    if match:
        return match.group(1).strip()
    return raw_data.strip()

def kickoff():
    """
    Run the flow.
    """
    CodeWriterFlow().kickoff()
    print("\n=== Flow Complete ===")
    print("Open output/code.py to view it.")

def plot():
    flow = CodeWriterFlow()
    flow.plot("code_writer_flow")
    print("Flow visualization saved to code_writer_flow.html")

if __name__ == "__main__":
    kickoff()