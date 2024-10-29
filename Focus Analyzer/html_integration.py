from bs4 import BeautifulSoup

def replace_placeholders(script_content: str, placeholder_mapping: dict) -> str:
    for placeholder, value in placeholder_mapping.items():
        script_content = script_content.replace(placeholder, str(value))
    return script_content

def generate_html_from_template(template_path: str, chart_data: dict, scores: dict, table_data: list) -> str:
    with open(template_path, "r", encoding="utf-8") as file:
        soup = BeautifulSoup(file, "html.parser")

    # Replace placeholders in the script tag
    script_tag = soup.find("script", text=lambda x: x and "__LABELS_LINECHART__" in x)
    if script_tag and script_tag.string:
        placeholder_mapping = {
            "__LABELS_LINECHART__": chart_data["line_chart"]["labels"],
            "__DATA_LINECHART__": chart_data["line_chart"]["data"],
            "__LABELS_PIECHART1__": chart_data["pie_chart1"]["labels"],
            "__DATA_PIECHART1__": chart_data["pie_chart1"]["data"],
            "__LABELS_PIECHART2__": chart_data["pie_chart2"]["labels"],
            "__DATA_PIECHART2__": chart_data["pie_chart2"]["data"],
            "__LABELS_PIECHART3__": chart_data["pie_chart3"]["labels"],
            "__DATA_PIECHART3__": chart_data["pie_chart3"]["data"],
        }
        updated_script_content = replace_placeholders(script_tag.string, placeholder_mapping)
        script_tag.string = updated_script_content

    # Update score cards
    score_cards = {
        "Final Score": scores["final"],
        "Max Score": scores["highest_continuous"],
        "Min score": scores["min"],
        "Score after quiz": scores["after_quiz"],
    }
    for card_title, score_value in score_cards.items():
        card = soup.find("h5", text=card_title)
        if card:
            score_span = card.find_next("span", {"class": "h2 font-weight-bold mb-0"})
            if score_span:
                score_span.string = str(score_value)

    # Populate quiz results table
    table_body = soup.find("tbody")
    if table_body:
        table_body.clear()
        for row in table_data:
            new_row = soup.new_tag("tr")

            # Question cell
            question_cell = soup.new_tag("td")
            question_div = soup.new_tag("div", attrs={"class": "d-flex px-2 py-1 align-items"})
            question_inner_div = soup.new_tag("div", attrs={"class": "ms-4"})
            question_p = soup.new_tag("p", attrs={"class": "text-xs font-weight-bold mb-0"})
            question_p.string = "Question"
            question_h6 = soup.new_tag("h6", attrs={"class": "text-sm mb-0"})
            question_h6.string = row["question"]
            question_inner_div.append(question_p)
            question_inner_div.append(question_h6)
            question_div.append(question_inner_div)
            question_cell.append(question_div)
            new_row.append(question_cell)

            # Status cell
            status_cell = soup.new_tag("td")
            status_div = soup.new_tag("div")
            status_p = soup.new_tag("p", attrs={"class": "text-xs font-weight-bold mb-0"})
            status_p.string = "Wrong/Correct"
            status_h6 = soup.new_tag("h6", attrs={"class": "text-sm mb-0"})
            status_h6.string = row["status"]
            status_div.append(status_p)
            status_div.append(status_h6)
            status_cell.append(status_div)
            new_row.append(status_cell)

            # Score cell
            score_cell = soup.new_tag("td")
            score_div = soup.new_tag("div")
            score_p = soup.new_tag("p", attrs={"class": "text-xs font-weight-bold mb-0"})
            score_p.string = "Score"
            score_h6 = soup.new_tag("h6", attrs={"class": "text-sm mb-0"})
            score_h6.string = row["score"]
            score_div.append(score_p)
            score_div.append(score_h6)
            score_cell.append(score_div)
            new_row.append(score_cell)

            table_body.append(new_row)

    return str(soup)