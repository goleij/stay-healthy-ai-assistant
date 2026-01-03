// streamlit.js - Minimal Streamlit Component API shim (no bundler)
// Robust: learns componentId from URL (streamlit_component_id) and always posts back with both componentId and id.

(function () {
  const RENDER_EVENT = "streamlit:render";

  const params = new URLSearchParams(window.location.search);

  // ✅ Streamlit usually provides this:
  // ?streamlit_component_id=XXXX
  let componentId =
    params.get("streamlit_component_id") ||
    params.get("componentId") ||
    params.get("component_id") ||
    params.get("id") ||
    null;

  function isStreamlitPayload(data) {
    if (!data) return false;
    if (data.isStreamlitMessage === true) return true;
    return typeof data.type === "string" && data.type.startsWith("streamlit:");
  }

  function postMessageToStreamlit(msg) {
    window.parent.postMessage(
      {
        isStreamlitMessage: true,
        componentId: componentId,
        id: componentId, // ✅ some streamlit versions use "id"
        ...msg,
      },
      "*"
    );
  }

  function sendComponentReady() {
    postMessageToStreamlit({
      type: "streamlit:componentReady",
      apiVersion: 1,
    });
  }

  function sendFrameHeight(height) {
    const h =
      typeof height === "number"
        ? height
        : Math.max(
            document.documentElement.scrollHeight || 0,
            document.body.scrollHeight || 0
          );

    postMessageToStreamlit({
      type: "streamlit:setFrameHeight",
      height: h,
    });
  }

  function sendComponentValue(value) {
    postMessageToStreamlit({
      type: "streamlit:setComponentValue",
      dataType: "json",
      value,
    });
  }

  window.addEventListener("message", (event) => {
    const data = event && event.data;
    if (!isStreamlitPayload(data)) return;

    // If componentId was not in URL (rare), learn it from the first render message
    if (!componentId) {
      componentId = data.componentId || data.id || null;
    }

    const incomingId = data.componentId || data.id;
    if (componentId && incomingId && incomingId !== componentId) return;

    if (data.type === "streamlit:render") {
      const ev = new CustomEvent(RENDER_EVENT, { detail: data });
      window.dispatchEvent(ev);
    }
  });

  window.Streamlit = {
    RENDER_EVENT,
    setComponentReady: sendComponentReady,
    setFrameHeight: sendFrameHeight,
    setComponentValue: sendComponentValue,
    events: {
      addEventListener: (name, handler) => window.addEventListener(name, handler),
      removeEventListener: (name, handler) =>
        window.removeEventListener(name, handler),
    },
  };
})();
