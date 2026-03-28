from typing import List, Dict, Any, Tuple
from src.chunking import count_tokens

# Max tokens reserved for injected memories context in the prompt
MEMORY_TOKEN_BUDGET = 1500

def build_memory_context(scored_chunks: List[Dict[str, Any]], token_budget: int = MEMORY_TOKEN_BUDGET) -> Tuple[str,int,int]:
    """
        Pack the highest-scored chunks into a memory context string.
        Stops adding chunks once the token budget is reached.
        Returns:
        memory_text -- formatted string ready to inject into system prompt
        chunks_used -- how many chunks fit in the budget
        tokens_used -- exact tokens consumed by the memory block
    """
    lines = []
    tokens_used = 0
    chunks_used = 0
    
    for chunk in scored_chunks:
        chunk_text = chunk["content"].replace("\n", " ").strip()
        chunk_tokens = count_tokens(chunk_text)
        
        # If adding this chunk exceeds the budget, stop
        if tokens_used + chunk_tokens > token_budget:
            break
        
        # Add chunk to memory context
        lines.append(chunk_text)
        tokens_used += chunk_tokens
        chunks_used += 1
        
    if not lines:
        return "", 0, 0
    
    # Format as a labelled block the LLM can clearly see    
    memory_text = (
        "[RELEVANT MEMORY CONTEXT]\n"
        + "\n---\n".join(lines)
        + "\n[END MEMORY CONTEXT]"
    )
    return memory_text, chunks_used, tokens_used

def build_prompt_with_memory(system_prompt: str, user_message: str, memory_text: str, recent_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
        Assemble the full messages list to send to the LLM.
        Order: system (with memory) -> recent history -> current user message.
    """
    
    if memory_text:
        full_system_prompt = f"{system_prompt}\n\n{memory_text}"
    else:
        full_system_prompt = system_prompt
        
    messages = [{'role': 'system', 'content': full_system_prompt}]
    messages.extend(recent_history)
    messages.append({'role': 'user', 'content': user_message})
    return messages