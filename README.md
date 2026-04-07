# HRBuddy

HR Buddy is an application which is inspired by HR Chatbot portals. Uses combination of Llama (LLM) + Nomic (Embedding) models. Uses Retrieval Augumented Generation for identify the context strictly from the HR Policies PDF.

The whole architecture is explain with the below picture.

![Architecture](media/wiki/Flowchart_v1.3.png)

## Prerequisites

Before running the application, ensure your system has the following:
* **Docker & Docker Compose** installed.
* **Hardware:** Minimum 8GB RAM (16GB+ recommended) to run the Llama 3.2 model smoothly.
* **OS:** Linux or macOS (Windows users should use WSL2).

## Getting Started

If you are on MacOS / Linux, simply make the shell script executable

    chmod +x run.sh

Then, just run the shell script.

    ./run.sh

Note: If you have any other shell instead of bash, open the first line of run.sh and replace the first line with the shell of your choice.

This script will handle all the setup of Ollama Package and the model and as well as builds the docker container.

## Tech Stack

* **Frontend:** Streamlit
* **AI/LLM:** Ollama (Llama 3.2 3B)
* **Embeddings:** Nomic Embed Text
* **Vector Store:** ChromaDB
* **Database:** MongoDB (for user authentication and chat history)
* **Orchestration:** Langchain & Docker

## Customizing the HR Policy

By default, the application uses the provided 2016 HR Manual. To use your own data:
1. Delete the existing PDF in the `rag_source/` directory.
2. Place your company's HR policy PDF into `rag_source/`.
3. Update the `PDF_PATH` variable in `main.py` if the filename changes.
4. Restart the containers to trigger a fresh vector embedding.

## Troubleshooting

**Ollama Connection Refused inside Docker:**
If the Streamlit app cannot reach Ollama, you need to configure Ollama to listen to the Docker bridge network.
1. Run `sudo systemctl edit ollama.service`
2. Add the following under the `[Service]` block:
   `Environment="OLLAMA_HOST=0.0.0.0"`
3. Save, then run `sudo systemctl daemon-reload` and `sudo systemctl restart ollama`.

## Author
**ToastCoder** * GitHub: [@ToastCoder](https://github.com/ToastCoder)
