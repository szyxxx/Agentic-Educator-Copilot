import operator
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END

class RemedialState(TypedDict):
    student_id: str
    course_id: str
    quiz_history: List[dict]
    weak_topics: List[str]
    current_cpmk_attainment: dict
    recommended_materials: List[dict]
    remedial_tasks: List[dict]
    personalized_study_plan: str
    messages: Annotated[list, operator.add]

def gap_analysis_node(state: RemedialState):
    print("Analyzing learning gaps...")
    return {}

def retrieve_materials_node(state: RemedialState):
    print("Retrieving relevant materials via RAG...")
    return {"recommended_materials": [{"topic": t, "source": "m1"} for t in state.get("weak_topics", [])]}

def generate_tasks_node(state: RemedialState):
    print("Generating personalized remedial tasks...")
    return {"remedial_tasks": [{"task": "Read chapter 4 and summarize."}]}

def study_plan_node(state: RemedialState):
    print("Creating personalized study plan...")
    return {"personalized_study_plan": "Focus on Agent concepts for 2 hours today."}

def notify_node(state: RemedialState):
    print("Notifying student with remedial plan...")
    return {}

def build_remedial_graph():
    graph = StateGraph(RemedialState)
    
    graph.add_node("analyze_learning_gaps", gap_analysis_node)
    graph.add_node("retrieve_relevant_materials", retrieve_materials_node)
    graph.add_node("generate_remedial_tasks", generate_tasks_node)
    graph.add_node("create_study_plan", study_plan_node)
    graph.add_node("notify_student", notify_node)
    
    graph.set_entry_point("analyze_learning_gaps")
    graph.add_edge("analyze_learning_gaps", "retrieve_relevant_materials")
    graph.add_edge("retrieve_relevant_materials", "generate_remedial_tasks")
    graph.add_edge("generate_remedial_tasks", "create_study_plan")
    graph.add_edge("create_study_plan", "notify_student")
    graph.add_edge("notify_student", END)
    
    return graph.compile()
