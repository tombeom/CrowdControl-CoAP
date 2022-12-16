import tkinter
import logging
import asyncio
from aiocoap import *
from tkinter import scrolledtext
from tkinter.constants import END

global serverAdr # CoAP Server IPv6 Address
global serverDir # CoAP Server Path (Directory)
global putMsg # PUT Message to CoAP Server

def btnGet():
    asyncio.run(coapGet())

def btnPut():
    asyncio.run(coapPut())

def btnObserve():
    asyncio.run(coapObserve())

def btnClearMessage():
    receivedMessage.delete('1.0', END)

async def coapGet():
    global serverAdr
    global serverDir
    serverAdr = coapServerAdrMessage.get()
    serverDir = coapServerDirMessage.get()

    protocol = await Context.create_client_context()

    request = Message(code=GET, uri='coap://' + serverAdr + serverDir)

    try:
        response = await protocol.request(request).response
    except Exception as e:
        receivedMessage.delete('1.0', END)
        receivedMessage.insert(END, 'Failed to fetch resource:\n')
        receivedMessage.insert(END, e)
    else:
        printMsg = "\n" + str(response.code) + "\n" + str(response.payload)[1:] + "\n"
        receivedMessage.insert(END, printMsg)

async def coapPut():
    global serverAdr
    global serverDir
    global putMsg
    serverAdr = coapServerAdrMessage.get()
    serverDir = coapServerDirMessage.get()
    putMsg = coapPutMessage.get().encode()

    context = await Context.create_client_context()
    await asyncio.sleep(2)
    request = Message(code=PUT, payload=putMsg, uri='coap://' + serverAdr + serverDir)

    try:
        response = await context.request(request).response
    except Exception as e:
        receivedMessage.delete('1.0', END)
        receivedMessage.insert(END, 'Failed to fetch resource:\n')
        receivedMessage.insert(END, e)
    else:
        printMsg = "\n" + str(response.code) + "\n" + str(response.payload)[1:] + "\n"
        receivedMessage.insert(END, printMsg)

async def coapObserve():
    global serverAdr
    global serverDir
    serverAdr = coapServerAdrMessage.get()
    serverDir = coapServerDirMessage.get()

    protocol = await Context.create_client_context()

    request = Message(code=GET, uri='coap://' + serverAdr + serverDir, observe=0)

    pr = protocol.request(request)
    
    response = await pr.response

    print("First response: %s\n%r"%(response, response.payload))
    printMsg = "\n\nFirst Response : " + str(response.code) + "\n" + str(response.payload)[1:] + "\n"
    receivedMessage.insert(END, printMsg)

    async for response in pr.observation:
        print("Next result: %s\n%r"%(response, response.payload))
        printMsg = "\nNext Response : " + str(response.code) + "\n" + str(response.payload)[1:] + "\n"
        receivedMessage.insert(END, printMsg)
        pr.observation.cancel()
        break

logging.basicConfig(level=logging.INFO)

mainWindow = tkinter.Tk()
mainWindow.title('Overwatch System')
mainWindow.geometry('800x600')
mainWindow.resizable(False, False)

titleLabel = tkinter.Label(mainWindow, text='Crowd Control Program that Communication with CoAP Server that uses Camera')
titleLabel.place(x=180, y=30)

receivedMessage = tkinter.scrolledtext.ScrolledText(mainWindow, width=100, height=20)
receivedMessage.place(x=50, y=80)
receivedMessage.insert(1.0, 'Receive Message from CoAP Server.')

coapServerAdrLabel = tkinter.Label(mainWindow, text='Server Address')
coapServerAdrLabel.place(x=110, y=360)

coapServerAdrMessage = tkinter.Entry(mainWindow, width=50)
coapServerAdrMessage.place(x=225, y=360)
coapServerAdrMessage.insert(tkinter.END, '192.168.1.31')

coapServerDirLabel = tkinter.Label(mainWindow, text='Server Directory')
coapServerDirLabel.place(x=110, y=400)

coapServerDirMessage = tkinter.Entry(mainWindow, width=50)
coapServerDirMessage.place(x=225, y=400)
coapServerDirMessage.insert(tkinter.END, '/.well-known/core')

coapPutLabel = tkinter.Label(mainWindow, text='PUT Message to Server')
coapPutLabel.place(x=90, y=440)

coapPutMessage = tkinter.Entry(mainWindow, width=50)
coapPutMessage.place(x=225, y=440)

btnCoapGet = tkinter.Button(mainWindow, width=10, height=2, text='GET', command=btnGet)
btnCoapGet.place(x=250, y=480)

btnCoapPut = tkinter.Button(mainWindow, width=10, height=2, text='PUT', command=btnPut)
btnCoapPut.place(x=365, y=480)

btnCoapObserve = tkinter.Button(mainWindow, width=10, height=2, text='OBSERVE', command=btnObserve)
btnCoapObserve.place(x=480, y=480)

btnClear = tkinter.Button(mainWindow, width=30, height=1, text='CLEAR ALL MESSAGES', command=btnClearMessage)
btnClear.place(x=300, y=540)

mainWindow.mainloop()