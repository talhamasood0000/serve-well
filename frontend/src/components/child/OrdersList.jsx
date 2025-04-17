import React from 'react';
import { Icon } from "@iconify/react/dist/iconify.js";

const OrdersList = ({ orders }) => {
    const getStatusClass = (status) => {
        switch(status.toLowerCase()) {
            case 'completed':
                return 'bg-success-100 text-success-600';
            case 'processing':
                return 'bg-warning-100 text-warning-600';
            case 'pending':
                return 'bg-info-100 text-info-600';
            case 'cancelled':
                return 'bg-danger-100 text-danger-600';
            default:
                return 'bg-neutral-100 text-secondary-light';
        }
    };

    return (
        <div className="col-12">
            <div className="card h-100 p-0">
                <div className="card-header border-bottom bg-base py-16 px-24 d-flex justify-content-between align-items-center">
                    <h6 className="text-lg fw-semibold mb-0">Orders List</h6>
                    <div className="d-flex gap-2">
                        <button className="btn btn-sm btn-outline-primary">
                            <Icon icon="solar:filter-linear" className="menu-icon me-2" />
                            Filter
                        </button>
                        <button className="btn btn-sm btn-primary">
                            <Icon icon="solar:add-circle-linear" className="menu-icon me-2" />
                            Add Order
                        </button>
                    </div>
                </div>
                <div className="card-body p-0 bg-base">
                    <div className="table-responsive">
                        <table className="table table-theme mb-0">
                            <thead>
                                <tr>
                                    <th className="fw-semibold text-secondary-light">Order #</th>
                                    <th className="fw-semibold text-secondary-light">Customer</th>
                                    <th className="fw-semibold text-secondary-light">Date</th>
                                    <th className="fw-semibold text-secondary-light">Status</th>
                                    <th className="fw-semibold text-secondary-light">Amount</th>
                                    <th className="fw-semibold text-secondary-light">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {orders.map((order) => (
                                    <tr key={order.id} className="table-row-theme">
                                        <td>{order.orderNumber}</td>
                                        <td>{order.customer}</td>
                                        <td>{order.date}</td>
                                        <td>
                                            <span className={`px-8 py-4 radius-4 ${getStatusClass(order.status)}`}>
                                                {order.status}
                                            </span>
                                        </td>
                                        <td>{order.amount}</td>
                                        <td>
                                            <div className="d-flex gap-2">
                                                <button className="btn btn-sm btn-outline-primary px-8 py-4">
                                                    <Icon icon="solar:eye-linear" className="text-lg" />
                                                </button>
                                                <button className="btn btn-sm btn-outline-success px-8 py-4">
                                                    <Icon icon="solar:pen-linear" className="text-lg" />
                                                </button>
                                                <button className="btn btn-sm btn-outline-danger px-8 py-4">
                                                    <Icon icon="solar:trash-bin-trash-linear" className="text-lg" />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
                {/* Changed from bg-white to bg-base to support theme switching */}
                <div className="card-footer bg-base py-16 px-24">
                    <div className="d-flex justify-content-between align-items-center">
                        <p className="mb-0 text-sm text-secondary-light">Showing 1-5 of 25 orders</p>
                        <div className="d-flex gap-2">
                            <button className="btn btn-sm btn-outline-primary px-12">Previous</button>
                            <button className="btn btn-sm btn-primary px-12">Next</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default OrdersList;