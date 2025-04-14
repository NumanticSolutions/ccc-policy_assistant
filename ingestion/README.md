<h1><img src=".././data/images/Numantic Solutions_Logomark_orange.png" alt="NS" style="float:left;width:70px;height:40px;"> $\textsf{\color{#ed8428}{Ingestion}}$ </h1>

## Overview

This folder contains the tools for raw data ingestion. This data ingestion is primarily done by crawling websites and retrieving text, PDF and in some cases CSV data.

Apr 14, 2025

## Configuration

The ```crawl_configuration.csv``` file contains the configuration for seed URLs. Seed URLs provide the starting sites for web crawls which depending on depth and width crawls can crawl many web pages using URL links found on these pages.

#### Crawl_configuration data dictionary:

| **Column**      | **Description**                                                                                                                                                 | 
|-----------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| seed_url        | The starting URL from which to crawl a website                                                                                                                  |
| storage_folder  | The sub-directory name for storage of the crawl results                                                                                                         |
| crawl_urls      | A list of specific URLs to crawl from this site; If this is blank, the crawler should look for HTML links on each web page.                                     |
| dont_crawl_urls | A list of specific URLs that should not be crawled from this website.  If this is blank, the crawler should crawl HTML links within depth and width parameters. |
| crawl_depth     | The number of page levels down from the seed to crawl.                                                                                                          |
| crawl_width     | The number of page levels across from each URL to crawl.                                                                                                        |


## Data Sources

At this time not all of these data sources have been ingested, but this list provides a good example of the types of sources we believe will be helpful to this policy assistant.

| **Source**                                                                                                                           | **Description**                                                                                                                                                                                   | 
|--------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Wikipedia](https://en.wikipedia.org/wiki/California_Community_Colleges)                                                             | Wikipedia provides a free online encyclopedia including content on California Community Colleges.                                                                                                 | 
| [Legislative Analyst’s Office](https://lao.ca.gov/)                                                                                  | The Legislative Analyst's Office (LAO) provides fiscal and policy advice to the California Legislature.                                                                                           | 
| [Community College League of California](https://www.ccleague.org/)                                                                  | The Community College League of California provides advocacy, professional development, and other supports to all 73 districts and 116 colleges in California.                                    | 
| [California Community Colleges](https://www.cccco.edu/)                                                                              | The California Community Colleges website provides information on all California Community Colleges.                                                                                              | 
| [California Community College Association for Occupational Education](https://cccaoe.org/)                                           | The California Community College Association for Occupational Education organization serves as a statewide advocate for administrators and educators working in vocational education.             | 
| [National Center for Education Statistics (NCES) – IPEDS](https://nces.ed.gov/ipeds/)                                                | The Integrated Postsecondary Education Data System (IPEDS) provides comprehensive data on community college enrollment, graduation rates, financial aid, and more.                                | 
| [Community College Research Center (CCRC) - Columbia University](https://ccrc.tc.columbia.edu/)                                      | The Community College Research Center provides research on student outcomes, transfer rates, and policy analysis.                                                                                 | 
| [American Association of Community Colleges (AACC)](https://www.aacc.nche.edu/)                                                      | The American Association of Community Colleges provides reports and fact sheets on student demographics, funding, and workforce development.                                                      |
| [U.S. Department of Education - College Scorecard](https://collegescorecard.ed.gov/)                                                 | The U.S. Department of Education provides data on graduation rates, student debt, and earnings outcomes for each community college.                                                               | 
| [National Student Clearinghouse Research Center](https://nscresearchcenter.org/)                                                     | The National Student Clearinghouse Research Center reports on college enrollment trends, transfer rates, and degree completion.                                                                   | 
| [The Aspen Institute - College Excellence Program](https://highered.aspeninstitute.org/)                                             | The Aspen Institute's College Excellence Program focuses on improving student success and institutional effectiveness in community colleges.                                                      |
| [Education Commission of the States (ECS)](https://www.ecs.org/)                                                                     | The Education Commission of the States (ECS) provides policy reports on community college funding and governance.                                                                                 | 
| [Integrated Postsecondary Education Data System (IPEDS) - National Center for Education Statistics (NCES)](https://nces.ed.gov/ipeds) | The Integrated Postsecondary Education Data System (IPEDS) provides data from a system of interrelated annual NCES surveys covering colleges, universities and vocational/technical institutions. | 
| [Board Docs](https://boarddocs.com/) and selected college websites                                                                   | Board Docs and selected school websites provide information on board meetings including schedules and minutes                                                                                     |
| [Digital Democracy Cal Matters](https://calmatters.digitaldemocracy.org/)                                                            | Digital Democracy provides information on legislation in California.                                                                                                                              |

