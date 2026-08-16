from fastapi import APIRouter, HTTPException, Response
from sqlalchemy.orm import Session
from fastapi import Depends
from app.database import get_db
from app.repositories import widget_repo

router = APIRouter(tags=["public"])


@router.get("/widgets/{widget_id}/config")
def get_widget_config(widget_id: str, response: Response, db: Session = Depends(get_db)):
    widget = widget_repo.get_by_id_public(db, widget_id)
    if widget is None:
        raise HTTPException(status_code=404, detail="Widget not found")

    # Short-lived cache: config can change (owner edits it), so don't cache long.
    response.headers["Cache-Control"] = "public, max-age=60"

    return {
        "id": str(widget.id),
        "type": widget.type,
        "title": widget.title,
        "description": widget.description,
        "fields": widget.fields,
        "button_text": widget.button_text,
        "display": widget.display,
        "version": widget.version,
    }


@router.get("/widget.js")
def get_widget_script(response: Response):
    # Long-lived, "immutable" cache: this file rarely changes, and when it
    # does, bump WIDGET_JS_VERSION below so the URL/query changes too.
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    response.headers["Content-Type"] = "application/javascript"

    js = """
(function () {
  var script = document.currentScript;
  var widgetId = new URL(script.src).searchParams.get("id");
  if (!widgetId) return;

  var apiBase = new URL(script.src).origin;

  fetch(apiBase + "/widgets/" + widgetId + "/config")
    .then(function (res) { return res.json(); })
    .then(function (config) { renderWidget(config, apiBase); })
    .catch(function (err) { console.error("Widget failed to load:", err); });

  function renderWidget(config, apiBase) {
    var container = document.createElement("div");
    container.className = "embedded-widget";
    container.style.cssText = "font-family: sans-serif; max-width: 360px; padding: 16px; border: 1px solid #ddd; border-radius: 8px;";

    var title = document.createElement("h3");
    title.textContent = config.title;
    container.appendChild(title);

    if (config.description) {
      var desc = document.createElement("p");
      desc.textContent = config.description;
      container.appendChild(desc);
    }

    var form = document.createElement("form");
    var inputs = {};

    config.fields.forEach(function (field) {
      var label = document.createElement("label");
      label.textContent = field.label;
      label.style.display = "block";
      label.style.marginTop = "8px";

      var input = document.createElement("input");
      input.type = field.type || "text";
      input.name = field.name;
      input.required = !!field.required;
      input.style.cssText = "width: 100%; padding: 6px; margin-top: 4px; box-sizing: border-box;";
      inputs[field.name] = input;

      label.appendChild(input);
      form.appendChild(label);
    });

    // Honeypot field -- hidden from real users via CSS, bots often fill it anyway
    var honeypot = document.createElement("input");
    honeypot.type = "text";
    honeypot.name = "website";
    honeypot.tabIndex = -1;
    honeypot.autocomplete = "off";
    honeypot.style.cssText = "position:absolute; left:-9999px; width:1px; height:1px;";
    form.appendChild(honeypot);

    var submitBtn = document.createElement("button");
    submitBtn.type = "submit";
    submitBtn.textContent = config.button_text || "Submit";
    submitBtn.style.cssText = "margin-top: 12px; padding: 8px 16px; cursor: pointer;";
    form.appendChild(submitBtn);

    var statusMsg = document.createElement("p");
    statusMsg.style.marginTop = "8px";
    form.appendChild(statusMsg);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var data = { widget_id: widgetId, data: {}, website: honeypot.value };
      config.fields.forEach(function (field) {
        data.data[field.name] = inputs[field.name].value;
      });

      fetch(apiBase + "/submissions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      })
        .then(function (res) {
          if (res.ok) {
            statusMsg.textContent = "Thanks! Submitted successfully.";
            form.reset();
          } else {
            return res.json().then(function (err) {
              statusMsg.textContent = "Error: " + (err.detail || "submission failed");
            });
          }
        })
        .catch(function () {
          statusMsg.textContent = "Something went wrong. Please try again.";
        });
    });

    container.appendChild(form);
    script.parentNode.insertBefore(container, script.nextSibling);
  }
})();
"""
    return Response(content=js, media_type="application/javascript")