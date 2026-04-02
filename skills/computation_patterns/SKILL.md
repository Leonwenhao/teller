# Computation Patterns — Worked Examples for OfficeQA

> Reference file for the agent. Contains exact Python code patterns for every computation type that appears in OfficeQA questions.

## Pattern 1: Linear Regression Prediction

When the question says "predict using a basic linear regression fit" or "extrapolate using linear regression":

```python
import numpy as np
from scipy.stats import linregress

# Example: Predict 1999 value using 1990-1998 data
years = np.array([1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998])
values = np.array([45234, 47891, 49123, 51002, 52345, 53890, 55123, 56789, 58234])

slope, intercept, r_value, p_value, std_err = linregress(years, values)
prediction = slope * 1999 + intercept
print(f"Predicted value for 1999: {prediction:.2f}")
# Do NOT round during computation. Round only for final answer if needed.
```

**Critical:** Extract ALL data points from the documents BEFORE running regression. A missing or wrong data point changes the slope. Verify you have exactly the number of years specified in the question.

## Pattern 2: T-Statistic Computation

When the question asks for a t-statistic comparing two groups:

```python
from scipy.stats import ttest_ind

# Example: Compare average bond rates during WWII vs post-WWII
wwii_rates = [2.1, 2.3, 2.0, 2.4, 2.2]
post_wwii_rates = [1.8, 1.5, 1.9, 2.0, 1.7]

t_stat, p_value = ttest_ind(wwii_rates, post_wwii_rates)
print(f"T-statistic: {t_stat:.6f}")
# Report the t-statistic with full precision, let the 1% tolerance handle rounding
```

## Pattern 3: Growth Rate Calculation

```python
# Year-over-year growth rate
def growth_rate(old_value, new_value):
    if old_value == 0:
        return float('inf')  # Flag this — division by zero means extraction error
    return ((new_value - old_value) / old_value) * 100

# Average annual growth rate over a period
def avg_annual_growth(values):
    """values is a list of annual figures in chronological order"""
    rates = []
    for i in range(1, len(values)):
        rates.append(growth_rate(values[i-1], values[i]))
    return sum(rates) / len(rates)

# Compound annual growth rate (CAGR)
def cagr(start_value, end_value, n_years):
    return ((end_value / start_value) ** (1 / n_years) - 1) * 100
```

**Watch out:** The question may ask for "average annual growth rate" (arithmetic mean of year-over-year rates) or "compound annual growth rate" (geometric). Read the question carefully.

## Pattern 3b: Theil Index of Dispersion

```python
import numpy as np
values = np.array([v1, v2, v3, ...])  # your extracted data
mean_val = np.mean(values)
theil = np.mean((values / mean_val) * np.log(values / mean_val))
```

## Pattern 4: Ratio Computation

```python
# Simple ratio
ratio = numerator / denominator

# Percentage
percentage = (part / whole) * 100

# Per-capita or per-unit
per_unit = total / count
```

**Always verify both values are in the same unit before dividing.** If one is in millions and the other in thousands, convert first.

## Pattern 5: Multi-Year Summation

```python
# When question asks for a total over multiple years
# Extract each year's value individually, then sum
values_by_year = {
    1990: 45234,
    1991: 47891,
    1992: 49123,
    # ... etc
}

total = sum(values_by_year.values())
print(f"Total 1990-1992: {total}")
# Verify: does the question include both endpoints? "1990 to 1992 inclusive" = 3 years
```

## Pattern 6: Calendar Year from Monthly Data

When you need a calendar year total but the table shows monthly or quarterly data:

```python
# Calendar year = January through December
# If table shows fiscal year (Oct-Sep), sum the months differently
calendar_year_1940 = sum([
    jan_1940, feb_1940, mar_1940, apr_1940, may_1940, jun_1940,
    jul_1940, aug_1940, sep_1940, oct_1940, nov_1940, dec_1940
])

# Fiscal year 1940 (pre-1976) = July 1939 through June 1940
# Fiscal year 2024 (post-1976) = October 2023 through September 2024
```

## Pattern 7: Validation Check

Run this after every computation:

```python
def validate_answer(answer, question_text):
    """Basic sanity checks before submitting"""
    # Check for NaN or infinity
    if answer != answer or abs(answer) == float('inf'):
        print("ERROR: Answer is NaN or infinity — extraction likely failed")
        return False

    # Check plausibility (customize per question type)
    if "percent" in question_text.lower() and abs(answer) > 10000:
        print(f"WARNING: {answer}% seems implausibly large")

    if "million" in question_text.lower() and answer < 0 and "deficit" not in question_text.lower():
        print(f"WARNING: Negative value {answer} when question doesn't suggest deficit")

    return True
```

---

*Add new patterns as they're discovered during iteration. Every computation the agent needs should have a worked example here.*
