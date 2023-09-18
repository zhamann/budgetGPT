# BudgetGPT

BudgetGPT is a simple project that takes a **Intuit Mint** transactions export and an **OpenAI** api key to generate a list of ways that the user can reach their financial goals and make better financial decisions. 

### Features:
* Uses specific trends in the user's transaction list to generate this response.
* Allows user to ask more questions after analysis.
* Automatically calculates tokens to avoid max-tokens error.
* Processes CSV so that the export can be uploaded without modification.

### To-Do:
* Break transaction list into chunks for message feed