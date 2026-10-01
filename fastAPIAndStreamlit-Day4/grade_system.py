import streamlit as st

# Set up the title of the app
st.title("🎓 Student Grading System")
st.write("Enter a mark between 0 and 100 to calculate the corresponding grade.")

# Input widget for the mark (using number_input handles empty/invalid text states automatically)
# We set value=None so the field starts blank rather than defaulting to 0
mark = st.number_input(
    "Enter student mark:", 
    min_value=0, 
    max_value=100, 
    value=None, 
    step=1,
    placeholder="Type a number between 0 and 100..."
)

# Handle the evaluation when a mark is entered
if mark is not None:
    # 1. Edge Case Protection: Check for values out of bounds (Streamlit's widget handles this, but code validation adds a safe backup)
    if mark < 0 or mark > 100:
        st.error("🚨 Error: Please enter a valid mark strictly between 0 and 100.")
    else:
        # 2. Grade Determination Logic
        if 90 <= mark <= 100:
            grade = "A"
        elif 80 <= mark <= 89:
            grade = "B"
        elif 70 <= mark <= 79:
            grade = "C"
        elif 60 <= mark <= 69:
            grade = "D"
        else:
            grade = "E"
        
        # 3. Success Message Display
        st.success(f"✅ **Results Calculated!**")
        st.metric(label="Entered Mark", value=f"{mark} / 100")
        st.subheader(f"Resulting Grade: **{grade}**")
else:
    # Handle the empty/initial state cleanly without crashing
    st.info("💡 Please enter a mark above to see the grade.")
