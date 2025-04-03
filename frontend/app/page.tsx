"use client";
import { useState, useRef } from "react";
import { motion } from "framer-motion";
import { useDropzone } from "react-dropzone";
import { Upload, Loader } from "lucide-react";

export default function Home() {
  const [image, setImage] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { getRootProps, getInputProps } = useDropzone({
    accept: { "image/*": [] },
    noClick: true,
    onDrop: (acceptedFiles) => {
      const file = acceptedFiles[0];
      setImage(file);
      setPreview(URL.createObjectURL(file));
    },
  });

  const handlePaste = (event: ClipboardEvent) => {
    const items = event.clipboardData?.items;
    if (items) {
      for (let item of items) {
        if (item.type.startsWith("image")) {
          const file = item.getAsFile();
          if (file) {
            setImage(file);
            setPreview(URL.createObjectURL(file));
          }
        }
      }
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setImage(file);
      setPreview(URL.createObjectURL(file));
    }
  };

  const handleSearch = async () => {
    if (!image) return;
    setLoading(true);

    const formData = new FormData();
    formData.append("file", image);

    const res = await fetch("http://localhost:5000/search", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();
    console.log(data)
    setResults(data.similar_images);
    setLoading(false);
  };

  return (
    <div 
      className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-4 text-white"
      onPaste={handlePaste}
    >
      <motion.h1 
        className="text-4xl font-extrabold mb-6 drop-shadow-lg"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        Image Similarity Search
      </motion.h1>

      <div className="flex flex-col items-center gap-4">
        <div {...getRootProps()} onClick={() => fileInputRef.current?.click()} className="border-2 border-dashed rounded-lg p-10 text-center bg-white shadow-lg cursor-pointer w-96 text-gray-700">
          <input {...getInputProps()} style={{ display: "none" }} />
          {preview ? (
            <img src={preview} alt="Preview" className="h-48 mx-auto rounded-lg shadow-md" />
          ) : (
            <div className="flex flex-col items-center">
              <Upload size={40} className="text-gray-500" />
              <p className="text-gray-500 mt-2">Paste an image or drag & drop or <span className="text-blue-600 cursor-pointer" onClick={() => fileInputRef.current?.click()}>click here to upload</span></p>
            </div>
          )}
        </div>
      </div>

      <input 
        type="file" 
        accept="image/*" 
        ref={fileInputRef} 
        onChange={handleFileChange} 
        className="hidden" 
      />

      {preview && (
        <motion.button 
          onClick={handleSearch}
          className="mt-6 px-6 py-2 bg-white text-blue-600 font-semibold rounded-lg shadow-md cursor-pointer hover:bg-gray-200 transition-all"
          whileTap={{ scale: 0.95 }}
        >
          {loading ? <Loader className="animate-spin" /> : "Find Similar Images"}
        </motion.button>
      )}

      {results.length > 0 && (
        <div className="mt-8 grid grid-cols-2 md-grid-cols-3 lg:grid-cols-4 gap-4">
          {results.map((url, idx) => (
            <motion.img
              key={idx}
              // src={`http://127.0.0.1:5000/${url}`} 
              src={`http://127.0.0.1:5000/static/images/${url.split('/').pop()}`}
              className="w-40 h-40 object-cover rounded-lg shadow-lg border-2 border-white"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
            />
          ))}
        </div>
      )}
    </div>
  );
}
