import streamlit as st
from datetime import date, timedelta
import numpy as np
import pandas as pd

# Constants
STOCKS_RETURN = 0.113
BONDS_RETURN = 0.046
CASH_RETURN = 0.041
RISK_FREE_RATE = 0.02
STOCKS_VOLATILITY = 0.15
BONDS_VOLATILITY = 0.05
CASH_VOLATILITY = 0.02
CUSHION_PERCENTAGE = 0.15  # 15% cushion

# We only define END_ALLOCATION now, as START_ALLOCATION will be calculated
END_ALLOCATION = {
    'stocks': 20,  # Conservative allocation for when funds are needed
    'bonds': 43,
    'cash': 37
}

# Define maximum allocation percentages for the start
MAX_START_STOCKS = 80  # Maximum stocks allocation at start
MAX_START_BONDS = 70   # Maximum bonds allocation at start
MIN_START_CASH = 5     # Minimum cash allocation at start

def calculate_start_allocation(time_horizon: int) -> dict:
    """
    Calculate starting allocation based on time horizon and end allocation.
    Uses a more conservative approach suitable for education savings.
    """
    # Calculate years remaining factor (0 to 1)
    time_factor = min(time_horizon / 10, 1)  # Cap at 10 years for max aggressiveness
    
    # Calculate starting stocks allocation
    start_stocks = min(
        END_ALLOCATION['stocks'] + (MAX_START_STOCKS - END_ALLOCATION['stocks']) * time_factor,
        MAX_START_STOCKS
    )
    
    # Calculate starting bonds allocation
    start_bonds = min(
        END_ALLOCATION['bonds'] + (MAX_START_BONDS - END_ALLOCATION['bonds']) * time_factor * 0.7,
        MAX_START_BONDS
    )
    
    # Ensure minimum cash allocation
    start_cash = max(MIN_START_CASH, 100 - start_stocks - start_bonds)
    
    # Adjust bonds to make total 100%
    start_bonds = 100 - start_stocks - start_cash
    
    return {
        'stocks': round(start_stocks, 2),
        'bonds': round(start_bonds, 2),
        'cash': round(start_cash, 2)
    }

def generate_glide_path(time_horizon: int) -> list:
    """Generate a glide path for portfolio allocation."""
    start_allocation = calculate_start_allocation(time_horizon)
    glide_path = []
    
    for year in range(time_horizon + 1):
        stocks = start_allocation['stocks'] + (END_ALLOCATION['stocks'] - start_allocation['stocks']) * year / time_horizon
        bonds = start_allocation['bonds'] + (END_ALLOCATION['bonds'] - start_allocation['bonds']) * year / time_horizon
        cash = start_allocation['cash'] + (END_ALLOCATION['cash'] - start_allocation['cash']) * year / time_horizon
        
        glide_path.append({
            'year': year,
            'stocks': round(stocks, 2),
            'bonds': round(bonds, 2),
            'cash': round(cash, 2)
        })
    return glide_path

def calculate_required_deposit(goal: float, years: int, start_allocation: dict) -> float:
    """Calculate required annual deposit based on goal and returns."""
    if years <= 0:
        return goal
    
    guess = goal / years
    
    def calculate_final_value(deposit: float) -> float:
        value = 0
        for _ in range(years):
            value += deposit
            stocks = value * (start_allocation['stocks'] / 100) * (1 + STOCKS_RETURN)
            bonds = value * (start_allocation['bonds'] / 100) * (1 + BONDS_RETURN)
            cash = value * (start_allocation['cash'] / 100) * (1 + CASH_RETURN)
            value = stocks + bonds + cash
        return value
    
    low, high = 0, goal * 2
    for _ in range(20):  # Binary search for optimal deposit
        guess = (low + high) / 2
        final_value = calculate_final_value(guess)
        if abs(final_value - goal) < 0.01:
            break
        if final_value < goal:
            low = guess
        else:
            high = guess
    return guess

def calculate_portfolio_projections(annual_deposit: float, time_horizon: int, glide_path: list) -> list:
    """Calculate year-by-year portfolio projections."""
    projections = []
    portfolio_value = 0
    
    for year in range(1, time_horizon + 1):
        # Add annual deposit
        portfolio_value += annual_deposit
        
        # Get current year's allocation
        allocation = glide_path[year - 1]
        
        # Calculate individual asset values
        stocks_value = portfolio_value * (allocation['stocks'] / 100)
        bonds_value = portfolio_value * (allocation['bonds'] / 100)
        cash_value = portfolio_value * (allocation['cash'] / 100)
        
        # Apply returns
        stocks_after_return = stocks_value * (1 + STOCKS_RETURN)
        bonds_after_return = bonds_value * (1 + BONDS_RETURN)
        cash_after_return = cash_value * (1 + CASH_RETURN)
        
        # Update portfolio value
        portfolio_value = stocks_after_return + bonds_after_return + cash_after_return
        
        projections.append({
            'year': year,
            'deposit': annual_deposit,
            'portfolio_value': portfolio_value,
            'stocks_value': stocks_after_return,
            'bonds_value': bonds_after_return,
            'cash_value': cash_after_return
        })
    
    return projections

def main():
    st.title("Education Savings Calculator")
    st.write("Plan your education savings with dynamic portfolio allocation")
    
    with st.form("savings_calculator"):
        col1, col2 = st.columns(2)
        
        with col1:
            annual_tuition = st.number_input(
                "Annual Tuition Cost ($)",
                min_value=1000.0,
                max_value=100000.0,
                value=20000.0,
                step=1000.0
            )
            
            years_in_university = st.number_input(
                "Number of Years in University",
                min_value=1,
                max_value=10,
                value=4
            )
        
        with col2:
            start_date = st.date_input(
                "When do you want to start saving?",
                min_value=date.today(),
                value=date.today()
            )
            
            university_start_date = st.date_input(
                "When does university start?",
                min_value=date.today(),
                value=date.today() + timedelta(days=365*4)
            )
        
        inflation_rate = st.slider(
            "Expected Annual Inflation Rate (%)",
            min_value=0.0,
            max_value=20.0,
            value=2.0,
            step=0.1
        ) / 100
        
        submitted = st.form_submit_button("Calculate Savings Plan")
    
    if submitted:
        if start_date >= university_start_date:
            st.error("Start date must be before university start date")
            return
        
        # Calculate time horizon
        time_horizon = round((university_start_date - start_date).days / 365.25)
        
        # Calculate total tuition cost
        total_tuition = annual_tuition * years_in_university
        
        # Calculate cushion (15% of total tuition)
        cushion_savings = total_tuition * CUSHION_PERCENTAGE
        
        # Calculate total savings goal
        total_savings_goal = total_tuition + cushion_savings
        
        # Calculate starting allocation
        start_allocation = calculate_start_allocation(time_horizon)
        
        # Generate glide path
        glide_path = generate_glide_path(time_horizon)
        
        # Calculate recommended deposit
        recommended_deposit = calculate_required_deposit(
            total_savings_goal,
            time_horizon,
            start_allocation
        )
        
        # Calculate projections
        projections = calculate_portfolio_projections(
            recommended_deposit,
            time_horizon,
            glide_path
        )
        
        # Display results
        st.header("Savings Plan Results")
        
        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Annual Deposit Needed", f"${recommended_deposit:,.2f}")
        with col2:
            st.metric("Total Savings Goal", f"${total_savings_goal:,.2f}")
        with col3:
            st.metric("Time Horizon", f"{time_horizon} years")
        
        # Starting allocation
        st.subheader("Starting Portfolio Allocation")
        st.write(f"Based on your {time_horizon}-year time horizon, here's your recommended starting allocation:")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Stocks", f"{start_allocation['stocks']}%")
        with col2:
            st.metric("Bonds", f"{start_allocation['bonds']}%")
        with col3:
            st.metric("Cash", f"{start_allocation['cash']}%")
        
        # Glide path visualization
        st.subheader("Investment Glide Path")
        glide_path_df = pd.DataFrame(glide_path)
        st.line_chart(glide_path_df[['stocks', 'bonds', 'cash']])
        
        # Portfolio projection visualization
        st.subheader("Portfolio Value Projection")
        projection_df = pd.DataFrame(projections)
        st.line_chart(projection_df['portfolio_value'])
        
        # Detailed projections table
        st.subheader("Year-by-Year Projections")
        st.dataframe(pd.DataFrame(projections).round(2))

if __name__ == "__main__":
    main()
