
## Financial Report Q&A System (RAG Pipeline)
**Tech Stack:** Python, HuggingFace (sentence-transformers), LangChain, ChromaDB, pdfplumber, Google Gemini API
**Tags:** #python #ai #rag #llm #huggingface #nlp #fintech #vector-database
**Description:** A Retrieval-Augmented Generation (RAG) system that answers natural-language questions over DAX company annual reports (Siemens, BMW, etc.), grounding every answer in the actual filing text instead of model memory — a smaller-scale mirror of production financial-document-intelligence tools.
**Key Highlights:**
- Engineered a PDF extraction pipeline (`pdfplumber`) that parses company/year metadata from filenames, extracts text page-by-page, and flags scanned/image-only pages needing OCR — with per-file error isolation so one corrupted PDF doesn't halt a batch run.
- Built a chunking stage (LangChain `RecursiveCharacterTextSplitter`) that splits extracted text into overlapping, metadata-tagged chunks (company, year, source file, chunk ID), preparing the corpus for embedding.
- Designing a structured extraction mode constraining LLM output to a strict JSON schema (revenue, net income, equity, key risks), enabling downstream financial ratio calculations (ROE, profit margin, debt-to-equity) computed in plain Python rather than trusting LLM arithmetic.
- Planned: HuggingFace sentence-transformer embeddings + ChromaDB vector storage + a LangChain RetrievalQA chain (Gemini), combining free-text Q&A and structured financial data extraction in one pipeline.


### AI CV Generator (Job Application Automator)
- **Tech Stack:** Python, Google Gemini API (Flash 3.6), xhtml2pdf, Streamlit, Markdown
- **Tags:** #python #ai #automation #api-integration #software-engineering #llm
- **Description:** Developed a privacy-focused, local automation tool that leverages LLMs to generate highly tailored resumes and cover letters directly from an Obsidian knowledge vault.
- **Key Highlights:**
	* Architected a secure, "human-in-the-loop" data pipeline that strips Personal Identifiable Information (PII) prior to API calls and dynamically re-injects it during local PDF assembly.
	* Integrated the Google Gemini API with advanced prompt engineering to dynamically parse unstructured markdown notes and map relevant technical skills to specific job descriptions.
	* Engineered a custom Python backend utilizing `xhtml2pdf` and CSS to automatically convert and render accepted markdown drafts into stylized, professional PDF documents.


### STM32 Embedded State Machine and Timer Controller
* **Tech Stack:** C, STM32 Microcontroller, Hardware Timers, Embedded Systems
* **Tags:** #embedded-systems, #c-programming, #microcontrollers, #stm32, #hardware
* **Description:** Designed and implemented a robust, timer-driven finite state machine (FSM) for a multi-functional hardware input handler.
* **Key Highlights:**
  - Applied low-level C programming principles and timer logic to process precise duration-based button inputs (e.g., long press for start/reset, short press for pause).
  - Developed an optimized software debouncing module to accurately filter out noise and accidental transient presses.
  - Implemented efficient hardware debugging and reliable state transitions without blocking the main CPU.

### Image-based Recognition Model “Apple vs. Tomato”
* **Tech Stack:** Python, YOLOv8, Ultralytics, Computer Vision
* **Tags:** #python, #computer-vision, #machine-learning, #ai, #data-science
* **Description:** Developed and trained a custom object detection model capable of highly accurate classification and distinction between apples and tomatoes.
* **Key Highlights:**
  - Configured and trained a custom YOLOv8 detection architecture using the Ultralytics framework.
  - Handled custom dataset preparation and evaluation to ensure the model could effectively distinguish features specific to both fruits.
  - Gained practical, hands-on knowledge of modern computer vision pipelines and deep learning libraries.

### Autonomous Arduino Mop Bot
* **Tech Stack:** Arduino (C++), Onshape (CAD), 3D Printing, Sensor Integration
* **Tags:** #robotics, #c-plus-plus, #cad, #mechatronics, #hardware-design
* **Description:** Designed, manufactured, and programmed a fully autonomous floor-mopping robot capable of real-time obstacle avoidance.
* **Key Highlights:**
  - Designed a custom robot chassis from scratch using Onshape CAD and manufactured it via 3D printing to securely house electronics and drag a microfiber mopping cloth.
  - Programmed autonomous navigation logic on an Arduino UNO, integrating a front-facing ultrasonic sensor for real-time obstacle detection and dynamic pivot maneuvering.
  - Successfully integrated hardware and software components, including the microcontroller, motor drivers, sensors, and power supply, into a functional mechatronics system.