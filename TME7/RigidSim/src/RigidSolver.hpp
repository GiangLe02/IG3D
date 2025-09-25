// ----------------------------------------------------------------------------
// RigidSolver.hpp
//
//  Created on: 18 Dec 2020
//      Author: Kiwon Um
//        Mail: kiwon.um@telecom-paris.fr
//
// Description: Simple Rigid Body Solver (DO NOT DISTRIBUTE!)
//
// Copyright 2020-2024 Kiwon Um
//
// The copyright to the computer program(s) herein is the property of Kiwon Um,
// Telecom Paris, France. The program(s) may be used and/or copied only with
// the written permission of Kiwon Um or in accordance with the terms and
// conditions stipulated in the agreement/contract under which the program(s)
// have been supplied.
// ----------------------------------------------------------------------------

#ifndef _RIGIDSOLVER_HPP_
#define _RIGIDSOLVER_HPP_

#include <glm/ext/matrix_transform.hpp>

#include "Vector3.hpp"
#include "Matrix3x3.hpp"
#include "Quad4.hpp"

struct BodyAttributes {
  BodyAttributes() :
    X(0, 0, 0), R(Mat3f::I()), P(0, 0, 0), L(0, 0, 0),
    V(0, 0, 0), omega(0, 0, 0), F(0, 0, 0), tau(0, 0, 0) {}

  glm::mat4 worldMat() const
  {
    return glm::mat4(           // column-major
      R(0,0), R(1,0), R(2,0), 0,
      R(0,1), R(1,1), R(2,1), 0,
      R(0,2), R(1,2), R(2,2), 0,
      X[0],   X[1],   X[2],   1);
  }

  tReal M;                      // mass
  Mat3f I0, I0inv;              // inertia tensor and its inverse in body space
  Mat3f Iinv;                   // inverse of inertia tensor

  // rigid body state
  Vec3f X;                      // position
  Mat3f R;                      // rotation
  Vec3f P;                      // linear momentum
  Vec3f L;                      // angular momentum

  // auxiliary quantities
  Vec3f V;                      // linear velocity
  Vec3f omega;                  // angular velocity

  // force and torque
  Vec3f F;                      // force
  Vec3f tau;                    // torque
  Quad4f q;                     //quaternion
  // mesh's vertices in body space
  std::vector<Vec3f> vdata0;
};

class Box : public BodyAttributes {
public:
  explicit Box(
    const tReal w=1.0, const tReal h=1.0, const tReal d=1.0, const tReal dens=10.0,
    const Vec3f v0=Vec3f(0, 0, 0), const Vec3f omega0=Vec3f(0, 0, 0), const Quad4f q0=Quad4f(0,0,0,0)) :
    width(w), height(h), depth(d)
  {
    V = v0;                     // initial velocity
    omega = omega0;             // initial angular velocity
    // q = q0;                     // initial quaternion
    tReal s = 0.5 * sqrt(1+R.v00+R.v11+R.v22);
    tReal x = (R.v21 - R.v12)/(4*s);
    tReal y = (R.v02 - R.v20)/(4*s); 
    tReal z = (R.v10 - R.v01)/(4*s);
    q = Quad4f(s,x,y,z);  // initial quaternion

    // TODO: calculate physical attributes
    // mass = density * width * height * depth
    M = dens * w * h * d;

    //Inertia tensor in body space
    tReal I_x = (1.0/12.0)*M*(h*h+d*d);
    tReal I_y = (1.0/12.0)*M*(w*w+d*d);
    tReal I_z = (1.0/12.0)*M*(h*h+w*w);

    I0 = Mat3f( I_x, 0, 0,
                0, I_y, 0,
                0, 0, I_z);
    
    // Inverse inertia tensor in body space
    I0inv = I0.inverse();
    
    // Inverse inertia tensor in world space
    Iinv = R * I0inv * R.transposed();

    // vertices data (8 vertices)
    // body space
    vdata0.push_back(Vec3f(-0.5*w, -0.5*h, -0.5*d));
    vdata0.push_back(Vec3f( 0.5*w, -0.5*h, -0.5*d));
    vdata0.push_back(Vec3f( 0.5*w,  0.5*h, -0.5*d));
    vdata0.push_back(Vec3f(-0.5*w,  0.5*h, -0.5*d));

    vdata0.push_back(Vec3f(-0.5*w, -0.5*h,  0.5*d));
    vdata0.push_back(Vec3f( 0.5*w, -0.5*h,  0.5*d));
    vdata0.push_back(Vec3f( 0.5*w,  0.5*h,  0.5*d));
    vdata0.push_back(Vec3f(-0.5*w,  0.5*h,  0.5*d));
  }

  // rigid body property
  tReal width, height, depth;
};

class RigidSolver {
public:
  explicit RigidSolver(
    BodyAttributes *body0=nullptr, const Vec3f g=Vec3f(0, 0, 0)) :
    body(body0), _g(g), _step(0), _sim_t(0) {}

  void init(BodyAttributes *body0)
  {
    body = body0;
    _step = 0;
    _sim_t = 0;
  }

  void step(const tReal dt)
  {
    std::cout << "t=" << _sim_t << " (dt=" << dt << ")" << std::endl;

    computeForceAndTorque();

    // TODO: time integration
    // update X, R, P, L
    // make sure your linear motion and don't care about angular motion handling first
    /* x(t+dt) = x(t) + dt* P(t)/M  */
    body->X += dt* body->P/body->M;

    /* P(t+dt) = P(t) + dt*F(t) */
    body->P += dt* body->F;
    body->V = body->P / body->M;

    /* R(t+dt) = R(t) + dt*(Rt* inverse_I0* Rt.T * L) x R(t) */
    body->omega = body->R * body->I0inv * body->R.transposed() * body->L;
    Quad4f omega2 = Quad4f(0, body->omega.x, body->omega.y, body->omega.z);
    body->q += dt* 0.5 * omega2.quaternionProduct(body->q);
    body->q.normalized();
    body->R = body->q.rotationMatrix();
    // before quaternion: body->R += dt* body->omega.crossProductMatrix() * body->R;

    /* L(t+dt) = L(t) + dt*tau */
    body->L += dt*body->tau;
    ++_step;
    _sim_t += dt;
  }

  BodyAttributes *body;

private:
  void computeForceAndTorque()
  {
    // TODO: force and torque calculation
    body->F = Vec3f(0, 0, 0);
    body->tau = Vec3f(0, 0, 0);

    /* F = mg */
    body->F = body->M * _g; // gravity
    // TODO: instance force at the very first step
    if(_step==1) {
      Vec3f instanceF = Vec3f(0.15,0.25,0.03);
      body->F += instanceF;
      Vec3f vdata0_w = body->R * body->vdata0[0] + body->X;
      body->tau = (vdata0_w - body->X).crossProduct(body->F);
    }
  }

  // simulation parameters
  Vec3f _g;                     // gravity
  tIndex _step;                 // step count
  tReal _sim_t;                 // simulation time
};

#endif  /* _RIGIDSOLVER_HPP_ */
