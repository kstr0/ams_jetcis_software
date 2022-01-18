// *****************************************************************************
//
// Copyright (c) 2018, Pleora Technologies Inc., All rights reserved.
//
// *****************************************************************************

#include "Defines.h"
#include "MyEventSink.h"
#include "Utilities.h"

#include <limits>


///
/// \brief Constructor
///

MyEventSink::MyEventSink( IPvRegisterEventSink *aRegisterEventSink )
    : mRegisterEventSink( aRegisterEventSink )
{
}



///
/// \brief Destructor
///

MyEventSink::~MyEventSink()
{

}



