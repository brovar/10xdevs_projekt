import React from 'react';
import PropTypes from 'prop-types';
import { Card, ListGroup } from 'react-bootstrap';

/**
 * Component that displays user profile information
 */
const UserProfileInfo = ({ userData }) => {
  if (!userData) {
    return (
      <Card className="mb-4">
        <Card.Body className="text-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
        </Card.Body>
      </Card>
    );
  }

  const { email, role, status, firstName, lastName, createdAt } = userData;

  // No need to translate roles anymore, using English directly
  const translateRole = (role) => {
    return role;
  };

  // No need to translate statuses anymore, using English directly
  const translateStatus = (status) => {
    return status;
  };

  return (
    <Card className="mb-4">
      <Card.Header as="h5">Profile Information</Card.Header>
      <ListGroup variant="flush">
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">Email:</div>
            <div className="col-md-8">{email}</div>
          </div>
        </ListGroup.Item>
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">First Name:</div>
            <div className="col-md-8">{firstName || "-"}</div>
          </div>
        </ListGroup.Item>
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">Last Name:</div>
            <div className="col-md-8">{lastName || "-"}</div>
          </div>
        </ListGroup.Item>
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">Role:</div>
            <div className="col-md-8">{translateRole(role)}</div>
          </div>
        </ListGroup.Item>
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">Status:</div>
            <div className="col-md-8">{translateStatus(status)}</div>
          </div>
        </ListGroup.Item>
        <ListGroup.Item>
          <div className="row">
            <div className="col-md-4 fw-bold">Created At:</div>
            <div className="col-md-8">{createdAt}</div>
          </div>
        </ListGroup.Item>
      </ListGroup>
    </Card>
  );
};

UserProfileInfo.propTypes = {
  userData: PropTypes.shape({
    id: PropTypes.string.isRequired,
    email: PropTypes.string.isRequired,
    role: PropTypes.string.isRequired,
    status: PropTypes.string.isRequired,
    firstName: PropTypes.string.isRequired,
    lastName: PropTypes.string.isRequired,
    createdAt: PropTypes.string.isRequired
  })
};

export default UserProfileInfo; 