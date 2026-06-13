import { useState } from "react";
import { api } from "../api/client";

export default function UploadCSV({ onUploaded }) {
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [message, setMessage] = useState("");

  const handleFile = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setStatus("uploading");
    const form = new FormData();
    form.append("file", file);
    try {
      const data = await api.post("/transactions/upload", form, true);
      setMessage(`✓ Imported ${data.imported} transactions`);
      setStatus("success");
      onUploaded?.();
    } catch (err) {
      setMessage(err.error || "Upload failed");
      setStatus("error");
    }
  };

  return (
    <div className="upload-box">
      <label htmlFor="csv-input" className="upload-label">
        <span>📂 Upload Bank Statement (CSV)</span>
        <input id="csv-input" type="file" accept=".csv" onChange={handleFile} hidden />
      </label>
      {status === "uploading" && <p className="status">Parsing & categorizing...</p>}
      {status === "success" && <p className="status success">{message}</p>}
      {status === "error" && <p className="status error">{message}</p>}
    </div>
  );
}