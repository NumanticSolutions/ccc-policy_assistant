<h1>$\textsf{\color{#ed8428}{California Community College Policy Assistant}}$ <img src="./data/images/Numantic Solutions_Logomark_orange.png" alt="NS" style="float:inline-end;width:100px;height:62px;"></h1>



## Overview

This an experimental chatbot employing Artificial Intelligence tools to help users easily improve their understanding of policy topics related to California's community colleges. The bot's target audience are stakeholders who would like to participate in community college decision making and would benefit from curated and detailed information related to community colleges. Some examples might include board members, administrators, staff, students, community activists or legislators.

By making this tool available, we hope to demonstrate how policy advocacy can be supported through the use of technology. If you want to learn more or have thoughts about this application or similar tools or the underlying technology, please reach out.

Feb 3, 2025

## Contact

[Numantic Solutions - numanticsolutions.com](https://numanticsolutions.com/)  
[California Community College Policy Assistant](https://ccc-polasst.numanticsolutions.com/)  
Email: Steve or Nathan at [info@numanticsolutions.com](info@numanticsolutions.com)



## Project status

This is an active project still in development, and there are frequent changes to this repository's contents and the Policy Assistant's functionality. The following table highlights our current key work areas and objectives.

| **Focus Area**                    | **Description**                                                             | **Objectives**                                                                                                                                                                            |
|-----------------------------------|-----------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Data source ingestion             | Data sources including web pages, PDF files and tabular data (eg CSV files) | <ol><li>Expand content base relevant to Community colleges</li><li>Clean content and add context and metadata</li><li>Store and vectorize content to facilitate future searches</li></ul> |
| Prompt construction               | Document retrieval and prompt construction exapanding on user questions     | <ol><li>Build robust content-retrieval tools </li><li>Construct effective LLM prompts</li></ul>                                                                                           |
| Model selection and configuration | Large Language Model (LLM) and parameter configuration                      | <ol><li>Identify LLM foundation most effective for this task </li><li>Determine most effective LLM configuration</li><li>Explore fine tuning the LLM</li></ul>                            |
| Performance measurement           | Chatbot quality assessment                                                  | <ol><li>Expand question and answer evaluation data</li><li>Extend testing framework to all components</li><li>Establish a continuous user-feedback loop</li></ul>                         |

## User Interface

A working prototype can be found at [ccc-polasst.numanticsolutions.com](https://ccc-polasst.numanticsolutions.com/).
<img src="./data/images/ccc-polasst_screenshot.png" alt="User Interface" width="1200"/>

## Architecure

Although this tool is underdevelopment and its architecture is likely to change, here is a good depiction of the current technological architecture.
<img src="./data/images/CCC_PolAsst_Architecture_Diagram_v1.png" alt="User Interface" width="1200"/>

## Technology

Although this tool is underdevelopment and its technological components are likely to change, here are some current key technologies.

### Technological Components

- Coding Language: [Python](https://www.python.org/)
- RAG Framework: [LangChain](https://www.langchain.com)
- Vector Database: [Chroma](https://www.trychroma.com/)
- Embedding Model: [Text-embedding-004](https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/text-embeddings-api)
- AI Large language Model (LLM): [Gemini-1.5-pro](https://ai.google.dev/gemini-api/docs/models/gemini))
- Document & Vector Storage: [Google Cloud Storage](https://cloud.google.com/?hl=en)
- User Interface: [Google Cloud Run](https://cloud.google.com/?hl=en)

### Data Sources

At this time not all of these data sources have been ingested, but this list provides a good example of the types of sources we believe will be helpful to this policy assistant.

 **Source**                                                               | **Description**                                                                                                                                                                       | 
|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Wikipedia](https://en.wikipedia.org/wiki/California_Community_Colleges) | Wikipedia provides a free online encyclopedia including content on California Community Colleges.                                                                                     | 
| [Legislative Analyst’s Office](https://lao.ca.gov/) | The Legislative Analyst's Office (LAO) provides fiscal and policy advice to the California Legislature.                                                                               | 
| [Community College League of California](https://www.ccleague.org/) | The Community College League of California provides advocacy, professional development, and other supports to all 73 districts and 116 colleges in California.                        | 
| [California Community Colleges](https://www.cccco.edu/) | The California Community Colleges website provides information on all California Community Colleges.                                                                                  | 
| [California Community College Association for Occupational Education](https://cccaoe.org/) | The California Community College Association for Occupational Education organization serves as a statewide advocate for administrators and educators working in vocational education. | 
| [National Center for Education Statistics (NCES) – IPEDS](https://nces.ed.gov/ipeds/) | The Integrated Postsecondary Education Data System (IPEDS) provides comprehensive data on community college enrollment, graduation rates, financial aid, and more.                    | 
| [Community College Research Center (CCRC) - Columbia University](https://ccrc.tc.columbia.edu/) | The Community College Research Center provides research on student outcomes, transfer rates, and policy analysis.                                                                     | 
| [American Association of Community Colleges (AACC)](https://www.aacc.nche.edu/) | The American Association of Community Colleges provides reports and fact sheets on student demographics, funding, and workforce development.                                          |
| [U.S. Department of Education - College Scorecard](https://collegescorecard.ed.gov/) | The U.S. Department of Education provides data on graduation rates, student debt, and earnings outcomes for each community college.                                                   | 
| [National Student Clearinghouse Research Center](https://nscresearchcenter.org/) | The National Student Clearinghouse Research Center reports on college enrollment trends, transfer rates, and degree completion.                                                       | 
| [The Aspen Institute - College Excellence Program](https://highered.aspeninstitute.org/) | The Aspen Institute's College Excellence Program focuses on improving student success and institutional effectiveness in community colleges.                                          | 
| [Urban Institute - Community College Research](https://www.urban.org/topics/education-and-training/community-colleges) | The Urban Institute's Community College Research group provides research on workforce development and financial aid policy.                                                           | 
| [Education Commission of the States (ECS)](https://www.ecs.org/) | The Education Commission of the States (ECS) provides policy reports on community college funding and governance.                                                                     | 
| [The Century Foundation - Higher Ed Policy](https://tcf.org/topics/education/) | The Century Foundation - Higher Ed Policy reports on community college equity, affordability, and student support programs.                                                           | 


