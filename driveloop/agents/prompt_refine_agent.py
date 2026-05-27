import json
import re
import traceback

import openai
from termcolor import colored


def _extract_json_object(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in LLM response.")
    return json.loads(text[start:end + 1])


def detect_prompt_language(prompt):
    """A lightweight detector used to keep refined prompts in the user's language."""
    if re.search(r"[\u4e00-\u9fff]", prompt):
        return "Chinese"
    if re.search(r"[\u3040-\u30ff]", prompt):
        return "Japanese"
    if re.search(r"[\uac00-\ud7af]", prompt):
        return "Korean"
    if re.search(r"[\u0400-\u04ff]", prompt):
        return "Russian"
    return "the same language as the original prompt"


class PromptRefineAgent:
    """Refine a user prompt using evaluation feedback without changing intent."""

    def __init__(self, model="gpt-4", max_prompt_chars=1200):
        self.model = model
        self.max_prompt_chars = max_prompt_chars

    def refine_prompt(self, original_prompt, current_prompt, evaluation_result, attempt_history):
        language = detect_prompt_language(original_prompt)
        history_for_prompt = [
            {
                "attempt_id": item.get("attempt_id"),
                "prompt": item.get("prompt"),
                "score": item.get("evaluation", {}).get("score"),
                "passed": item.get("evaluation", {}).get("passed"),
                "summary": item.get("evaluation", {}).get("summary"),
                "failure_reasons": item.get("evaluation", {}).get("failure_reasons", []),
            }
            for item in attempt_history[-3:]
        ]

        q0 = (
            "You are a prompt refinement agent for an autonomous-driving scene simulator. "
            "The simulator turns a natural-language user requirement into a video. "
            "An external autonomous-driving evaluation algorithm scored the video. "
            "Your job is to minimally refine the prompt so the next rendered video can score better."
        )
        q1 = (
            "Hard constraints: preserve the user's original intent; do not introduce a new scenario, "
            "new object category, new traffic participant, or safety-critical behavior unless it is a "
            "reasonable clarification of the original requirement; do not remove requested objects; "
            "do not contradict explicit position, motion, color, count, or viewpoint requirements."
        )
        q2 = (
            f"Return the refined prompt in {language}. If the original prompt is mixed-language, "
            "keep the same mixed-language style. The prompt should remain concise and directly usable by ChatSim."
        )
        q3 = (
            "Return only valid JSON with keys: "
            "'refined_prompt' (string), "
            "'preserved_requirements' (list of strings), "
            "'changed_aspects' (list of strings), "
            "'rationale' (string), "
            "'confidence' (float from 0 to 1)."
        )
        q4 = {
            "original_user_prompt": original_prompt[:self.max_prompt_chars],
            "current_prompt": current_prompt[:self.max_prompt_chars],
            "latest_evaluation": evaluation_result.to_dict(),
            "recent_attempt_history": history_for_prompt,
        }

        try:
            result = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": q0},
                    {"role": "user", "content": q1},
                    {"role": "user", "content": q2},
                    {"role": "user", "content": q3},
                    {"role": "user", "content": json.dumps(q4, ensure_ascii=False, indent=2)},
                ],
            )
            answer = result["choices"][0]["message"]["content"]
            refined = _extract_json_object(answer)
            if not refined.get("refined_prompt"):
                raise ValueError("LLM response missing refined_prompt.")
            print(
                f"{colored('[Prompt Refine Agent]', color='magenta', attrs=['bold'])} "
                f"{colored('[Refined Prompt>>>]', attrs=['bold'])} {refined['refined_prompt']}\n"
            )
            return refined
        except Exception as e:
            print(e)
            traceback.print_exc()
            return self._fallback_refinement(original_prompt, current_prompt, evaluation_result)

    def _fallback_refinement(self, original_prompt, current_prompt, evaluation_result):
        feedback_items = []
        if evaluation_result.summary:
            feedback_items.append(evaluation_result.summary)
        feedback_items.extend(evaluation_result.failure_reasons)
        feedback_items.extend(evaluation_result.suggestions)
        feedback = "; ".join(item for item in feedback_items if item)
        if not feedback:
            feedback = "improve the evaluation score while preserving the original request"

        refined_prompt = (
            f"{current_prompt}. Preserve the original user request exactly, while making the scene clearer, "
            f"the vehicle motion more stable, and the result easier for the autonomous-driving evaluator "
            f"to assess. Evaluation feedback: {feedback}"
        )

        return {
            "refined_prompt": refined_prompt,
            "preserved_requirements": [original_prompt],
            "changed_aspects": ["Added evaluator-oriented clarification without changing user intent."],
            "rationale": "Fallback refinement because LLM JSON parsing or API call failed.",
            "confidence": 0.35,
        }
