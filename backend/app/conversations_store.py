"""
Legal Document RAG Assistant - Conversations Persistence Store
-------------------------------------------------------------
Lightweight file-backed storage manager for conversations, messages, citations,
and search indexing.
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conversations.json")

def _load_data() -> Dict[str, Any]:
    if not os.path.exists(DATA_FILE):
        return {"conversations": {}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"conversations": {}}

def _save_data(data: Dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class ConversationsStore:
    def list_conversations(self) -> List[Dict[str, Any]]:
        data = _load_data()
        convs = list(data.get("conversations", {}).values())
        # Sort by updated_at descending
        convs.sort(key=lambda c: c.get("updated_at", ""), reverse=True)
        return [
            {
                "id": c["id"],
                "title": c.get("title", "Untitled Query"),
                "created_at": c.get("created_at"),
                "updated_at": c.get("updated_at"),
                "message_count": len(c.get("messages", [])),
                "last_message": c.get("messages", [])[-1]["text"] if c.get("messages") else ""
            }
            for c in convs
        ]

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        data = _load_data()
        return data.get("conversations", {}).get(conv_id)

    def create_conversation(self, title: str, user_query: str, assistant_response: Dict[str, Any]) -> Dict[str, Any]:
        data = _load_data()
        conv_id = f"conv_{uuid.uuid4().hex[:10]}"
        now = datetime.utcnow().isoformat() + "Z"

        messages = [
          {"id": 1, "sender": "user", "text": user_query},
          {
              "id": 2,
              "sender": "assistant",
              "text": assistant_response.get("answer", ""),
              "citations": assistant_response.get("citations", []),
              "refused": assistant_response.get("refused", False),
              "model_name": assistant_response.get("model_name", ""),
              "provider": assistant_response.get("llm_provider", "")
          }
        ]

        conv = {
            "id": conv_id,
            "title": title or user_query[:60],
            "created_at": now,
            "updated_at": now,
            "messages": messages
        }

        data.setdefault("conversations", {})[conv_id] = conv
        _save_data(data)
        return conv

    def add_message_to_conversation(self, conv_id: str, user_query: str, assistant_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        data = _load_data()
        convs = data.get("conversations", {})
        if conv_id not in convs:
            return self.create_conversation(user_query[:60], user_query, assistant_response)

        conv = convs[conv_id]
        now = datetime.utcnow().isoformat() + "Z"
        msg_id_base = len(conv.get("messages", [])) + 1

        conv["messages"].append({"id": msg_id_base, "sender": "user", "text": user_query})
        conv["messages"].append({
            "id": msg_id_base + 1,
            "sender": "assistant",
            "text": assistant_response.get("answer", ""),
            "citations": assistant_response.get("citations", []),
            "refused": assistant_response.get("refused", False),
            "model_name": assistant_response.get("model_name", ""),
            "provider": assistant_response.get("llm_provider", "")
        })
        conv["updated_at"] = now
        _save_data(data)
        return conv

    def update_title(self, conv_id: str, new_title: str) -> Optional[Dict[str, Any]]:
        data = _load_data()
        convs = data.get("conversations", {})
        if conv_id not in convs:
            return None
        convs[conv_id]["title"] = new_title
        convs[conv_id]["updated_at"] = datetime.utcnow().isoformat() + "Z"
        _save_data(data)
        return convs[conv_id]

    def delete_conversation(self, conv_id: str) -> bool:
        data = _load_data()
        convs = data.get("conversations", {})
        if conv_id in convs:
            del convs[conv_id]
            _save_data(data)
            return True
        return False

    def search(self, query_str: str) -> List[Dict[str, Any]]:
        if not query_str or not query_str.strip():
            return self.list_conversations()

        q = query_str.lower().strip()
        data = _load_data()
        convs = list(data.get("conversations", {}).values())

        results = []
        for c in convs:
            title_match = q in c.get("title", "").lower()
            matching_msgs = [m for m in c.get("messages", []) if q in m.get("text", "").lower()]

            if title_match or matching_msgs:
                snippet = ""
                if matching_msgs:
                    snippet = matching_msgs[0].get("text", "")[:120] + "..."
                elif c.get("messages"):
                    snippet = c["messages"][0].get("text", "")[:120] + "..."

                results.append({
                    "id": c["id"],
                    "title": c.get("title", "Untitled Query"),
                    "created_at": c.get("created_at"),
                    "updated_at": c.get("updated_at"),
                    "match_type": "title" if title_match else "content",
                    "snippet": snippet,
                    "message_count": len(c.get("messages", []))
                })

        results.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return results

conversations_store = ConversationsStore()
