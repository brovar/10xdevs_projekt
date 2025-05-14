import React from 'react';

const HomePage = () => {
  return (
    <div className="container my-4">
      <div className="jumbotron py-5 bg-light rounded-3">
        <div className="container-fluid py-3">
          <h1 className="display-5 fw-bold">Welcome to Steambay</h1>
          <p className="col-md-8 fs-4">
            Browse offers, buy and sell products on our e-commerce platform.
          </p>
          <div className="d-grid gap-2 d-md-flex justify-content-md-start">
            <button className="btn btn-primary btn-lg" type="button">
              Browse offers
            </button>
          </div>
        </div>
      </div>

      <div className="row mt-5">
        <div className="col-md-12 text-center">
          <h2>Latest offers</h2>
          <p>Latest offers will appear here.</p>
        </div>
      </div>
    </div>
  );
};

export default HomePage; 