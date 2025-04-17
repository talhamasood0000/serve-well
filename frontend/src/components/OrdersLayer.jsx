import React, { useState } from "react";
import { Icon } from "@iconify/react/dist/iconify.js";
import OrdersList from "./child/OrdersList";

const OrdersLayer = () => {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [orders, setOrders] = useState([
    { id: 1, orderNumber: "ORD-001", customer: "John Doe", date: "2023-10-15", status: "Completed", amount: "$125.00" },
    { id: 2, orderNumber: "ORD-002", customer: "Jane Smith", date: "2023-10-16", status: "Processing", amount: "$85.50" },
    { id: 3, orderNumber: "ORD-003", customer: "Robert Johnson", date: "2023-10-17", status: "Pending", amount: "$210.75" },
    { id: 4, orderNumber: "ORD-004", customer: "Emily Davis", date: "2023-10-18", status: "Cancelled", amount: "$45.20" },
    { id: 5, orderNumber: "ORD-005", customer: "Michael Wilson", date: "2023-10-19", status: "Completed", amount: "$150.00" }
  ]);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      
      // Preview for image files
      if (selectedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(selectedFile);
      } else {
        setPreview(null); // No preview for non-image files
      }
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      
      // Preview for image files
      if (droppedFile.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = (e) => setPreview(e.target.result);
        reader.readAsDataURL(droppedFile);
      } else {
        setPreview(null); // No preview for non-image files
      }
    }
  };

  const handleFileDelete = () => {
    setFile(null);
    setPreview(null);
  };

  return (
    <div className="row gy-4">
      <div className="col-12">
        <div className="card h-100 p-0">
          <div className="card-header border-bottom bg-base py-16 px-24">
            <h6 className="text-lg fw-semibold mb-0">Upload Orders</h6>
          </div>
          <div className="card-body p-24">
            <div className="d-flex align-items-center gap-3 mb-4">
              <div>
                <label
                  htmlFor="fileUpload"
                  className="text-sm fw-semibold text-primary-light mb-8"
                >
                  Upload CSV or Excel File
                </label>
                <div
                  id="fileUpload"
                  className="fileUpload image-upload"
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                >
                  <label
                    htmlFor="fileInput"
                    className="file-upload image-upload__box"
                  >
                    <div className="image-upload__boxInner custom">
                      {preview ? (
                        <>
                          <img
                            src={preview}
                            alt={file?.name}
                            className="image-upload__image"
                            height="30"
                          />
                          <button
                            type="button"
                            className="image-upload__deleteBtn"
                            onClick={handleFileDelete}
                          >
                            <i className="ri-close-line"></i>
                          </button>
                        </>
                      ) : (
                        <>
                          <i className="ri-upload-2-line image-upload__icon"></i>
                          <p className="text-xs text-secondary-light mt-4 mb-0">
                            Drag & drop file here
                          </p>
                        </>
                      )}
                    </div>
                    <input
                      type="file"
                      id="fileInput"
                      name="file"
                      hidden
                      onChange={handleFileChange}
                      accept=".csv, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/vnd.ms-excel"
                    />
                  </label>
                </div>
              </div>
              <button
                type="button"
                className="btn btn-primary d-flex align-items-center gap-8 px-20 flex-shrink-0 h-40-px mt-32"
              >
                Upload
                <Icon icon="solar:upload-linear" />
              </button>
            </div>
            {file && (
              <div className="mt-2">
                <p className="mb-0 text-sm">
                  <span className="fw-semibold">Selected file:</span> {file.name}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Orders List */}
      <OrdersList orders={orders} />
    </div>
  );
};

export default OrdersLayer;