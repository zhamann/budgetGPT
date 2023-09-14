# BudgetGPT

BudgetGPT is a simple project that takes a **Intuit Mint** transactions export and an **OpenAI** api key to generate a list of ways that the user can reach their financial goals and make better financial decisions. 

### Features:
* Uses specific trends in the user's transaction list to generate this response.
* Automatically calculates tokens to avoid max-tokens error.
* Processes CSV so that the export can be uploaded without modification.

### To-Do:
* Switch from single response to conversation based.
* Continue to optimize prompt for more detailed responses.
* Shorten general prompt text to include more transactions.