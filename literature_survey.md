# 2. LITERATURE SURVEY

An examination of existing academic and applied research in mental health support systems demonstrates an ongoing transition from traditional, face-to-face therapy to the use of technology-enhanced processes to optimise accessibility and ongoing care. Traditional counseling services and community-based support networks have been effective within specific localities or scheduled hours; however, they often have issues such as high costs, social stigma, delayed communications with professionals; and inconsistent availability. Digital technologies have increased the interaction between patients and providers, but many do not address the "last mile" issues associated with immediate crisis support; continuous monitoring; and real-time status updates [1]. The literature suggests that platforms with clearly defined roles for all stakeholders involved (user; psychologist; administrator), a continuous flow of information to all participating members, and real-time mood mapping generally provide more dependable platforms and build user trust. These conclusions have informed the development of the Mental Health Chatbot by placing a premium on providing operational transparency and establishing a systematic framework for communication rather than by focusing on overly complicated platform functions that result in limited utility.

## 2.1 Existing and Proposed System

### Existing System

*   The majority of mental health support occurs privately through scheduled therapy sessions, crisis hotlines, or informal coordination via support groups, which are often sporadic and dependent on provider availability [1][2].
*   Users are not often confirmed or informed on the specific metrics of their mental well-being (e.g., stress trends over time) thus reducing transparency of the recovery process and long-term trust in self-care strategies [3].
*   The beneficiaries (patients) have access to professional assistance irregularly and unpredictably, as there is no mechanism for 24/7 instant support or "talk therapy" during off-hours [4].
*   Volunteer or counselor coordination is maintained manually, making it hard to investigate patient history efficiently before a session [5].
*   The current initiatives do not offer a unified digital system to keep track of mood history, instant chat logs, and a confirmation that the user's distress signals are delivered to the intended psychologists for review [6].

### Proposed System

*   An online application will provide a centralized database and interface for Users, Psychologists, and Administrators.
*   The application will provide users with role-based workflow capabilities which define explicit duties and authority for each type of user (e.g., Psychologists can view dashboards, Users can chat).
*   It will provide users with information about the status of their mental health through visual analytics (charts) throughout the interaction cycle and will define whether critical stress levels have been detected.
*   Using Generative AI (Google Gemini), the application will determine the best immediate response to soothe the user as quickly as possible, acting as a first-responder.
*   All communication between users and the system will be in electronic format; this will increase accountability of data (logs) and help increase the success of future therapy sessions by providing history.

## 2.2 Feasibility Study

### 2.2.1 Technical Feasibility Study
*   The app is a web-based application built utilizing the **Django Framework** (Python) which allows for a robust, secure **codebase** to support both user interactions and administrative overhead, streamlining the development and continuous maintenance process.
*   **Google Gemini API** serves as the intelligence infrastructure, giving developers a scalable solution for natural language processing, sentiment analysis, and context-aware responses without the need for administrative knowledge of training local LLMs.
*   Real-time synchronization of records through **AJAX and Django ORM** allows all users (and assigned psychologists) to see updates to mood logs, chat history, and stress status as soon as they are made.
*   Django's native template engine provides robust support for the content-rich functionality on a very large selection of current mobile and desktop browsers.
*   The use of modular systems architecture will permit adding on additional features (for example: tools to analyze long-term depression trends) and/or enhanced psychologist matching features without disrupting any of the present system components.
*   The technology stack (the software used to build the application) has been developed from very popular and successful platforms with strong developer communities.

### 2.2.2 Operational Feasibility Study
*   The mental health support system is made to work with the existing practices of therapy: intake, monitoring, and analysis. Users do not need to change their behaviors in any significant manner to use this system.
*   The web interface provides access to the chatbot system for all users from their devices, eliminating the requirement for separate or additional infrastructure.
*   Real-time mood notifications and dashboard updates will allow psychologists to coordinate effectively without having to make repetitive manual follow-ups with patients.
*   The administrative tools provide complete oversight of system use, all users that have been registered, and the activity of all participants. This will help ensure a smooth and consistent operation of the platform.
*   The easy-to-use platform will allow for a gradual transition in the adoption of AI assistance. With the gradual introduction of the system, users will have the opportunity to become comfortable with using the product.

### 2.2.3 Economic Feasibility Study
*   The creation of the Mental Health Chatbot has used many cost-effective technologies and has therefore avoided using costly proprietary and licensed software (e.g., using Open Source Python/Django).
*   Having access to a single unified **codebase** will significantly reduce the time spent developing, staffing, and maintaining over the long term.
*   By providing cloud-based AI services (Gemini), we can eliminate the need for physical GPU servers which will greatly reduce our costs of setup and operation.
*   The system will be able to be launched and tested early on with all cloud services being free or extremely low cost (tier-based), thus significantly lowering our capital outlay in the beginning.

## 2.3 Tools and Technologies used
The Mental Health Chatbot was built with a current-day mobile-first Technology stack that allows for rapid development, and easy support for real-time communication, scalability, and maintenance. The selection of tools allows for easy development in multiple platforms with low infrastructure complexity and operational cost.

### 2.3.1 Python (Programming Language)
Python serves as the primary backend programming language. It is known for its readability and vast ecosystem of libraries, particularly in Data Science and AI, making it the perfect choice for integrating Machine Learning capabilities into a web app.

### 2.3.2 Django Framework
Django allows the user to create a web application that is built on one unified code base in the Python programming language. Django provides the fundamental **backend** functionality of user authentication/authorization, database management (ORM), and secure request handling. Its "batteries-included" philosophy ensures that security features like CSRF protection are enabled by default.

### 2.3.3 Google Gemini API (AI Services)
Google Gemini serves as the **intelligence** framework for the application. This tool provides the fundamental Generative AI functionality for understanding user input, generating empathetic responses, and performing sentiment analysis in real-time. The use of a managed API allows the developers great versatility because there are no dedicated AI model servers that have to be created and maintained.

### 2.3.4 Django Authentication
Django Authentication will be used for securely creating user accounts and signing into the application. It allows the use of role-based access control for users, psychologists, and administrators, ensuring that users only have access to functionality appropriate for their roles (e.g., only Psychologists can see the Mood Dashboard).

### 2.3.5 SQLite / PostgreSQL (Database)
The application uses a relational database to store user information, chat logs, mood scores, and survey results. The database's integration with Django's ORM allows for real-time **synchronisation** of data, enabling the system to persist conversation history and analytical data securely and efficiently.

### 2.3.6 Chart.js (Visualization)
Chart.js is used on the frontend to render dynamic graphs and charts. It powers the "Mood Insights" dashboard, visualizing the data stored in the database to provide psychologists with an instant overview of a patient's progress over time.

### 2.3.7 Development Tools
**Visual Studio Code** serves as the primary editing environment for developing the application. **Git** is used for managing builds and source code versioning, ensuring that the code meets the highest standards of quality throughout its life cycle.
