from langchain.prompts import PromptTemplate

template = """This is a question-answering system over the transcripts of videos, which provide tutorials and discussions on various programming topics.
Given sections of the transcripts for the videos, create an answer to the question "QUESTION" that references those sections as "SECTIONS".

- If the question can be answered by the information provided in "SECTIONS", include the value of the "source" property in the "metadata" for the section following the response (The value of the "source" property is a url link to a specific time in the video from which the section of the transcript came) like this:
Answer:
ANSWER

Source:
SOURCE
- If the question cannot be answered by the sections or from these instructions, the system should not answer the question. The system should respond with "Info could not be found within the video transcripts"
- Sections are taken from the middle of transcripts and may be truncated or missing context.
- Transcripts are not guaranteed to be relevant to the question.

QUESTION: {question}

SECTIONS:
{sources}
"""

main = PromptTemplate(template=template, input_variables=["sources", "question"])
