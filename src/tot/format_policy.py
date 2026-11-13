"""One controlled intervention: a phase-specific output-format system message.

No answer, score, proposal or label is synthesized or corrected by this module.
"""

POLICY_NAME = 'format_contract'


def format_instruction(messages):
    text = next(m['content'] for m in reversed(messages) if m['role'] == 'user')
    if text.rstrip().endswith('Possible next steps:'):
        return (
            'You are an arithmetic-step generator consumed by a strict program. '
            'Return at most FOUR distinct possible next operations, one per line. '
            'Use exactly this grammar: A OP B = C (left: REMAINING_NUMBERS). '
            'A and B must be two available numbers from the LAST Input in the user message; '
            'C is their result. REMAINING_NUMBERS includes C and all unused numbers, '
            'separated by single spaces, with no commas. Use ASCII + - * / only. '
            'Return only operation lines: no heading, numbering, bullets, Markdown, '
            'code fences, commentary or blank lines. Do not repeat the examples. '
            'If fewer than two numbers remain, return no operation.'
        )
    if text.startswith('Evaluate if given numbers'):
        return (
            'Evaluate only the LAST set of numbers in the user message. '
            'Return exactly one lowercase word: sure, likely, or impossible. '
            'Return no reasoning, punctuation, Markdown, additional lines or whitespace.'
        )
    if 'give a judgement' in text and 'Judge:' in text:
        return (
            'Judge only the LAST Input and Answer pair. '
            'Return exactly one lowercase word: sure or impossible. '
            'Return no reasoning, punctuation, Markdown, additional lines or whitespace.'
        )
    return (
        'Complete only the LAST puzzle using its reasoning steps. '
        'Return exactly one line: Answer: EXPRESSION = 24. '
        'EXPRESSION must use each of the four ORIGINAL input numbers exactly once, '
        'with ASCII + - * / and parentheses. Use the original numbers rather than '
        'only the intermediate results. Return no reasoning, Markdown or extra lines.'
    )
